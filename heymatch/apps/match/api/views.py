import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.chat.models import StreamChannel
from heymatch.apps.group.models import GroupMember, GroupProfilePhotoPurchased, GroupV2
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.payment.models import UserPointConsumptionHistory
from heymatch.shared.exceptions import (
    MatchRequestAlreadySubmittedException,
    MatchRequestGroupIsMineException,
    MatchRequestGroupIsNotMineException,
    MatchRequestHandleFailedException,
    MatchRequestNotFoundException,
    UserPointBalanceNotEnoughException,
)

from .serializers import (
    MatchRequestCreateBodySerializer,
    ReceivedMatchRequestSerializer,
    SentMatchRequestSerializer,
)

stream = settings.STREAM_CLIENT
onesignal_client = settings.ONE_SIGNAL_CLIENT

logger = logging.getLogger(__name__)


class MatchRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        # IsUserActive,
    ]

    serializer_class = ReceivedMatchRequestSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # Query MatchRequest (newest to oldest)
        # Exclude "CANCELED" MatchRequest
        gm_queryset = GroupMember.objects.filter(user=request.user, is_active=True)
        mr_sent_qs = (
            MatchRequest.active_objects.select_related()
            .filter(
                Q(
                    sender_group_id__in=list(
                        gm_queryset.values_list("group_id", flat=True)
                    )
                )
                & ~Q(status="CANCELED")
                & Q(is_active=True)
            )
            .order_by("-created_at")
        )
        mr_received_qs = (
            MatchRequest.active_objects.select_related()
            .filter(
                Q(
                    receiver_group_id__in=list(
                        gm_queryset.values_list("group_id", flat=True)
                    )
                )
                & ~Q(status="CANCELED")
                & Q(is_active=True)
            )
            .order_by("-created_at")
        )

        # Serialize
        mr_sent_serializer = SentMatchRequestSerializer(
            mr_sent_qs, many=True, context={"force_original_image": True}
        )
        mr_received_serializer = self.get_serializer(
            mr_received_qs, many=True, context={"force_original_image": True}
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
        2) Check if MatchRequest already created
        3) Check if user has enough balance or free_pass item.
        """
        to_group_id = request.data.get("to_group_id", None)
        from_group_id = request.data.get("from_group_id", None)
        if not to_group_id or not from_group_id:
            raise FieldDoesNotExist("All fields should be provided.")

        user = request.user

        # Permission class checks #1
        if GroupMember.objects.filter(
            user=user, is_active=True, group_id__in=[to_group_id]
        ).exists():
            raise MatchRequestGroupIsMineException()
        if not GroupMember.objects.filter(
            user=user, is_active=True, group_id__in=[from_group_id]
        ).exists():
            raise MatchRequestGroupIsNotMineException()

        group_qs = GroupV2.objects.all().filter(is_active=True)
        to_group = get_object_or_404(group_qs, id=to_group_id)
        from_group = get_object_or_404(group_qs, id=from_group_id)

        # Check #2
        user_groups_id = GroupMember.objects.filter(
            user=user, is_active=True
        ).values_list("group_id", flat=True)
        mr1_qs = MatchRequest.active_objects.select_related().filter(
            sender_group_id__in=list(user_groups_id), receiver_group_id=to_group_id
        )
        mr2_qs = MatchRequest.active_objects.select_related().filter(
            sender_group_id=to_group_id, receiver_group_id__in=list(user_groups_id)
        )
        if mr1_qs.exists() or mr2_qs.exists():
            raise MatchRequestAlreadySubmittedException()

        # Check #4
        # if user.free_pass and user.free_pass_active_until < timezone.now():
        #     mr = self.create_match_request(
        #         sender_group=from_group, receiver_group=to_group
        #     )
        #     # Create MatchRequest
        #     serializer = ReceivedMatchRequestSerializer(instance=mr)
        #     return Response(data=serializer.data, status=status.HTTP_200_OK)
        if user.point_balance < to_group.match_point:
            raise UserPointBalanceNotEnoughException()

        # Deduct point
        user.point_balance = user.point_balance - to_group.match_point
        user.save(update_fields=["point_balance"])

        # Record ConsumptionHistory
        UserPointConsumptionHistory.objects.create(
            user=user,
            consumed_point=to_group.match_point,
            consumed_reason=UserPointConsumptionHistory.ConsumedReasonChoice.SEND_MATCH_REQUEST,
        )

        # Create MatchRequest
        mr = self.create_match_request(sender_group=from_group, receiver_group=to_group)

        # Create GroupProfilePhotoPurchased
        gp = GroupProfilePhotoPurchased.objects.filter(
            buyer=request.user, seller=to_group
        )
        if not gp.exists():
            GroupProfilePhotoPurchased.objects.create(
                buyer=request.user, seller=to_group
            )

        # Send push notification
        to_group_user_ids = [
            str(user_id)
            for user_id in GroupMember.objects.filter(
                user__is_active=True, group_id__in=[to_group_id]
            ).values_list("user_id", flat=True)
        ]
        res = onesignal_client.send_notification_to_specific_users(
            title="매칭 요청이 왔어요!",
            content=f"[{from_group.title}] 그룹으로부터 매칭요청을 받았어요! 수락하면 바로 채팅할 수 있어요 😀",
            user_ids=to_group_user_ids,
            custom_data={
                "route_to": "MatchRequestPage",
                "extra": {"match_request_id": "test"},
            },
        )
        logger.debug(f"OneSignal response for Match request: {res}")

        serializer = ReceivedMatchRequestSerializer(
            instance=mr, context={"force_original_image": True}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def create_match_request(
        sender_group: GroupV2, receiver_group: GroupV2
    ) -> MatchRequest:
        return MatchRequest.objects.create(
            sender_group=sender_group,
            receiver_group=receiver_group,
        )

    @swagger_auto_schema(request_body=no_body)
    def accept(self, request: Request, match_request_id: int) -> Response:
        # Check validity
        mr = self.get_match_request_obj(match_request_id=match_request_id)
        self.is_user_receiver_group(match_request=mr)
        self.check_match_request_status(
            match_request=mr,
            target_status=MatchRequest.MatchRequestStatusChoices.WAITING,
        )  # WAITING

        # Update MatchRequest
        mr.status = MatchRequest.MatchRequestStatusChoices.ACCEPTED  # ACCEPTED
        mr.save(
            update_fields=[
                "status",
            ]
        )
        # Unlock photo
        group = mr.sender_group
        gps = GroupProfilePhotoPurchased.objects.filter(
            seller=group, buyer=request.user
        )
        if not gps.exists():
            GroupProfilePhotoPurchased.objects.create(seller=group, buyer=request.user)

        # Create Stream channel for both groups
        result = self.create_stream_channel(user_id=str(request.user.id), mr=mr)
        return Response(result, status.HTTP_200_OK)

    @staticmethod
    def create_stream_channel(
        user_id: str, mr: MatchRequest, send_push_notification=True
    ):
        # Create Stream channel for both groups
        receiver_group = mr.receiver_group
        receiver_group_member_qs = GroupMember.objects.filter(
            group=receiver_group, is_active=True
        )
        receiver_user_ids = [
            str(user_id)
            for user_id in receiver_group_member_qs.values_list("user_id", flat=True)
        ]
        sender_group = mr.sender_group
        sender_group_member_qs = GroupMember.objects.filter(
            group=sender_group, is_active=True
        )
        sender_user_ids = [
            str(user_id)
            for user_id in sender_group_member_qs.values_list("user_id", flat=True)
        ]
        channel = stream.channel(
            settings.STREAM_CHAT_CHANNEL_TYPE,
            None,
            data=dict(
                members=[*receiver_user_ids, *sender_user_ids],
                created_by_id=str(user_id),
            ),
        )
        # Note: query method creates a channel
        res = channel.query()

        # Save StreamChannel
        stream_channel_id = res["channel"]["id"]
        stream_channel_cid = res["channel"]["cid"]
        stream_channel_type = res["channel"]["type"]

        for receiver_gm in receiver_group_member_qs:
            StreamChannel.objects.create(
                stream_id=stream_channel_id,
                cid=stream_channel_cid,
                type=stream_channel_type,
                group_member=receiver_gm,
            )
        for sender_gm in sender_group_member_qs:
            StreamChannel.objects.create(
                stream_id=stream_channel_id,
                cid=stream_channel_cid,
                type=stream_channel_type,
                group_member=sender_gm,
            )
        # Send push notification
        if send_push_notification:
            res = onesignal_client.send_notification_to_specific_users(
                title="매칭 성공!!",
                content=f"[{receiver_group.title}] 그룹이 매칭요청을 수락했어요!! 지금 바로 메세지를 보내봐요 🎉",
                user_ids=sender_user_ids,
                custom_data={
                    "route_to": "MatchRequestPage",
                    "extra": {"match_request_id": "test"},
                },
            )
            logger.debug(f"OneSignal response for Match Success: {res}")
        return {
            "stream_chat_id": stream_channel_id,
            "stream_chat_cid": stream_channel_cid,
            "stream_chat_type": stream_channel_type,
        }

    @swagger_auto_schema(request_body=no_body)
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

        receiver_group = mr.receiver_group
        sender_group = mr.sender_group
        sender_group_member_qs = GroupMember.objects.filter(
            group=sender_group, is_active=True
        )
        sender_user_ids = [
            str(user_id)
            for user_id in sender_group_member_qs.values_list("user_id", flat=True)
        ]
        # Send push notification
        res = onesignal_client.send_notification_to_specific_users(
            title="아쉬워요..",
            content=f"[{receiver_group.title}] 그룹이 매칭요청을 거절했어요..😥 다른 그룹을 찾아봐요!",
            user_ids=sender_user_ids,
            custom_data={
                "route_to": "MatchRequestPage",
                "extra": {"match_request_id": "test"},
            },
        )
        logger.debug(f"OneSignal response for Match deny: {res}")
        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=no_body)
    def cancel(self, request: Request, match_request_id: int) -> Response:
        # Check validity
        mr = self.get_match_request_obj(match_request_id=match_request_id)
        self.is_user_sender_group(match_request=mr)
        self.check_match_request_status(
            match_request=mr,
            target_status=MatchRequest.MatchRequestStatusChoices.WAITING,
        )  # WAITING

        mr.status = MatchRequest.MatchRequestStatusChoices.CANCELED  # CANCELED
        mr.is_active = False
        mr.save(update_fields=["status", "is_active"])
        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def get_match_request_obj(match_request_id: int) -> MatchRequest:
        try:
            mr = MatchRequest.active_objects.get(id=match_request_id)
        except MatchRequest.DoesNotExist:
            raise MatchRequestNotFoundException()
        return mr

    def is_user_receiver_group(self, match_request: MatchRequest):
        if not GroupMember.objects.filter(
            user=self.request.user, group=match_request.receiver_group, is_active=True
        ).exists():
            raise MatchRequestHandleFailedException(
                extra_info="You are not receiver group"
            )

    def is_user_sender_group(self, match_request: MatchRequest):
        if not GroupMember.objects.filter(
            user=self.request.user, group=match_request.sender_group, is_active=True
        ).exists():
            raise MatchRequestHandleFailedException(
                extra_info="You are not sender group"
            )

    @staticmethod
    def check_match_request_status(match_request: MatchRequest, target_status: str):
        if not match_request.status == target_status:
            raise MatchRequestHandleFailedException(
                extra_info=f"Status should be '{target_status}'"
            )
