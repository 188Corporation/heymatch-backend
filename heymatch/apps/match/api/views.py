from typing import Any

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import Group
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.payment.models import UserPointConsumptionHistory
from heymatch.apps.user.models import User
from heymatch.shared.exceptions import (
    GroupNotWithinSameHotplaceException,
    MatchRequestAlreadySubmittedException,
    MatchRequestGroupIsMineException,
    MatchRequestHandleFailedException,
    MatchRequestNotFoundException,
    UserPointBalanceNotEnoughException,
)
from heymatch.shared.permissions import IsUserActive, IsUserJoinedGroup

from .serializers import (
    MatchRequestCreateBodySerializer,
    ReceivedMatchRequestSerializer,
    SentMatchRequestSerializer,
)

stream = settings.STREAM_CLIENT
onesignal_client = settings.ONE_SIGNAL_CLIENT


class MatchRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserJoinedGroup,
    ]

    serializer_class = ReceivedMatchRequestSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # Query MatchRequest (newest to oldest)
        # Exclude "CANCELED" MatchRequest
        joined_group_id = self.request.user.joined_group.id
        mr_sent_qs = (
            MatchRequest.active_objects.select_related()
            .filter(Q(sender_group_id=joined_group_id) & ~Q(status="CANCELED"))
            .order_by("-created_at")
        )
        mr_received_qs = (
            MatchRequest.active_objects.select_related()
            .filter(Q(receiver_group_id=joined_group_id) & ~Q(status="CANCELED"))
            .order_by("-created_at")
        )

        # Serialize
        mr_sent_serializer = SentMatchRequestSerializer(
            mr_sent_qs, many=True, context={"force_original": True}
        )
        mr_received_serializer = self.get_serializer(
            mr_received_qs, many=True, context={"force_original": True}
        )
        data = {
            "sent": mr_sent_serializer.data,
            "received": mr_received_serializer.data,
        }
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=MatchRequestCreateBodySerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        1) Check if user joined any group + if group_is mine
        2) Check if user does not belong to same hotplace of the other group.
        3) Check if MatchRequest already created
        4) Check if user has enough balance or free_pass item.
        """
        group_id = request.data.get("group_id", None)
        if not group_id:
            raise FieldDoesNotExist("`group_id` should be provided.")

        user = request.user

        # Permission class checks #1
        if group_id == user.joined_group.id:
            raise MatchRequestGroupIsMineException()

        group_qs = Group.active_objects.all()
        group = get_object_or_404(group_qs, id=group_id)
        # Check #2
        if user.joined_group.hotplace.id != group.hotplace.id:
            raise GroupNotWithinSameHotplaceException()

        # Check #3
        mr_qs = MatchRequest.active_objects.select_related().filter(
            sender_group_id=user.joined_group.id, receiver_group_id=group_id
        )
        if mr_qs.exists():
            raise MatchRequestAlreadySubmittedException()

        # Check #4
        if user.free_pass and user.free_pass_active_until < timezone.now():
            mr = self.create_match_request(
                sender_group=user.joined_group, receiver_group=group
            )
            # Create MatchRequest
            serializer = ReceivedMatchRequestSerializer(instance=mr)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        if user.point_balance < group.match_point:
            raise UserPointBalanceNotEnoughException()

        # Deduct point
        user.point_balance = user.point_balance - group.match_point
        user.save(update_fields=["point_balance"])

        # Record ConsumptionHistory
        UserPointConsumptionHistory.objects.create(
            user=user,
            consumed_point=group.match_point,
            consumed_reason=UserPointConsumptionHistory.ConsumedReasonChoice.SEND_MATCH_REQUEST,
        )

        # Create MatchRequest
        mr = self.create_match_request(
            sender_group=user.joined_group, receiver_group=group
        )

        # Send push notification
        receiver_user_id = User.active_objects.get(joined_group=group).id
        onesignal_client.send_notification_to_specific_users(
            message=f"'{user.joined_group.title}' 그룹이 매칭요청을 보냈어요! 수락하면 바로 채팅할 수 있어요 😀",
            user_ids=[receiver_user_id],
        )
        # TODO: handle OneSignal response

        serializer = ReceivedMatchRequestSerializer(instance=mr)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def create_match_request(
        sender_group: Group, receiver_group: Group
    ) -> MatchRequest:
        return MatchRequest.objects.create(
            sender_group=sender_group,
            receiver_group=receiver_group,
        )

    def accept(self, request: Request, match_request_id: int) -> Response:
        # Check validity
        mr = self.get_match_request_obj(match_request_id=match_request_id)
        self.is_user_receiver_group(match_request=mr)
        self.check_match_request_status(
            match_request=mr,
            target_status=MatchRequest.MatchRequestStatusChoices.WAITING,
        )  # WAITING

        # Create Stream channel for both groups
        sender_group = mr.sender_group
        sender_user = User.active_objects.get(joined_group=sender_group)
        channel = stream.channel(
            settings.STREAM_CHAT_CHANNEL_TYPE,
            None,
            data=dict(
                members=[str(request.user.id), str(sender_user.id)],
                created_by_id=str(request.user.id),
            ),
        )
        # Note: query method creates a channel
        res = channel.query()

        # Update MatchRequest
        mr.status = MatchRequest.MatchRequestStatusChoices.ACCEPTED  # ACCEPTED
        mr.stream_channel_id = res["channel"]["id"]
        mr.stream_channel_cid = res["channel"]["cid"]
        mr.stream_channel_type = res["channel"]["type"]
        mr.save(
            update_fields=[
                "status",
                "stream_channel_id",
                "stream_channel_cid",
                "stream_channel_type",
            ]
        )

        # Send push notification
        onesignal_client.send_notification_to_specific_users(
            message=f"[{request.user.joined_group.title}] 그룹이 매칭요청을 수락했어요!!🎉 지금 바로 메세지를 보내봐요 😆",
            user_ids=[sender_user.id],
        )
        # TODO: handle OneSignal response

        serializer = self.get_serializer(instance=mr)
        return Response(serializer.data, status.HTTP_200_OK)

    def reject(self, request: Request, match_request_id: int) -> Response:
        # Check validity
        mr = self.get_match_request_obj(match_request_id=match_request_id)
        self.is_user_receiver_group(match_request=mr)
        self.check_match_request_status(
            match_request=mr,
            target_status=MatchRequest.MatchRequestStatusChoices.WAITING,
        )  # WAITING

        mr.status = MatchRequest.MatchRequestStatusChoices.REJECTED  # REJECTED
        mr.save(update_fields=["status"])

        # Send push notification
        sender_group = mr.sender_group
        onesignal_client.send_notification_to_specific_users(
            message=f"[{request.user.joined_group.title}] 그룹이 매칭요청을 거절했어요..😥",
            user_ids=[sender_group.id],
        )
        # TODO: handle OneSignal response

        serializer = self.get_serializer(instance=mr)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def cancel(self, request: Request, match_request_id: int) -> Response:
        # Check validity
        mr = self.get_match_request_obj(match_request_id=match_request_id)
        self._is_user_sender_group(match_request=mr)
        self.check_match_request_status(
            match_request=mr,
            target_status=MatchRequest.MatchRequestStatusChoices.WAITING,
        )  # WAITING

        mr.status = MatchRequest.MatchRequestStatusChoices.CANCELED  # CANCELED
        mr.save(update_fields=["status"])
        serializer = self.get_serializer(instance=mr)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def get_match_request_obj(match_request_id: int) -> MatchRequest:
        try:
            mr = MatchRequest.active_objects.get(id=match_request_id)
        except MatchRequest.DoesNotExist:
            raise MatchRequestNotFoundException()
        return mr

    def is_user_receiver_group(self, match_request: MatchRequest):
        if not match_request.receiver_group.id == self.request.user.joined_group.id:
            raise MatchRequestHandleFailedException(
                extra_info="You are not receiver group"
            )

    def _is_user_sender_group(self, match_request: MatchRequest):
        if not match_request.sender_group.id == self.request.user.joined_group.id:
            raise MatchRequestHandleFailedException(
                extra_info="You are not sender group"
            )

    @staticmethod
    def check_match_request_status(match_request: MatchRequest, target_status: str):
        if not match_request.status == target_status:
            raise MatchRequestHandleFailedException(
                extra_info=f"Status should be '{target_status}'"
            )
