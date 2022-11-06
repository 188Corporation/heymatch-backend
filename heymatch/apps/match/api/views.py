from typing import Any

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import Group, GroupBlackList
from heymatch.apps.match.models import (
    MATCH_REQUEST_CHOICES,
    MatchRequest,
    StreamChannel,
)
from heymatch.apps.user.models import User
from heymatch.shared.exceptions import (
    GroupNotWithinSameHotplaceException,
    MatchRequestAlreadySubmittedException,
    MatchRequestHandleFailedException,
    MatchRequestNotFoundException,
    UserPointBalanceNotEnoughException,
)
from heymatch.shared.permissions import (
    IsUserActive,
    IsUserGroupLeader,
    IsUserJoinedGroup,
    IsUserJoinedGroupActive,
)

from .serializers import (
    MatchedGroupLeaderDetailSerializer,
    MatchRequestCreateBodySerializer,
    MatchRequestDetailSerializer,
    MatchRequestReceivedSerializer,
    MatchRequestSendBodySerializer,
    MatchRequestSentSerializer,
    ReceivedMatchRequestSerializer,
    SentMatchRequestSerializer,
)

stream = settings.STREAM_CLIENT


class MatchRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserJoinedGroup,
    ]

    # serializer_class = ReceivedMatchRequestSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # Query MatchRequest (newest to oldest)
        # Exclude "CANCELED" MatchRequest
        joined_group_id = self.request.user.joined_group.id
        mr_sent_qs = (
            MatchRequest.objects.select_related()
            .filter(Q(sender_group_id=joined_group_id) & ~Q(status="CANCELED"))
            .order_by("-created_at")
        )
        mr_received_qs = (
            MatchRequest.objects.select_related()
            .filter(Q(receiver_group_id=joined_group_id) & ~Q(status="CANCELED"))
            .order_by("-created_at")
        )

        # Serialize
        mr_sent_serializer = SentMatchRequestSerializer(mr_sent_qs, many=True)
        mr_received_serializer = ReceivedMatchRequestSerializer(
            mr_received_qs, many=True
        )
        data = {
            "sent": mr_sent_serializer.data,
            "received": mr_received_serializer.data,
        }
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=MatchRequestCreateBodySerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        1) Check if user joined any group.
        2) Check if user does not belong to same hotplace of the other group.
        3) Check if MatchRequest already created
        4) Check if user has enough balance or free_pass item.
        """
        group_id = request.data.get("group_id", None)
        if not group_id:
            raise FieldDoesNotExist("`group_id` should be provided.")

        group_qs = Group.active_objects.all()
        group = get_object_or_404(group_qs, id=group_id)
        user = request.user
        # Permission class checks #1
        # Check #2
        if user.joined_group.hotplace.id != group.hotplace.id:
            raise GroupNotWithinSameHotplaceException()

        # Check #3
        mr_qs = MatchRequest.objects.select_related().filter(
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

        # Create MatchRequest
        mr = self.create_match_request(
            sender_group=user.joined_group, receiver_group=group
        )
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
            match_request=mr, target_status=MATCH_REQUEST_CHOICES[0][0]
        )  # WAITING

        # Create Stream channel for group leaders for both groups
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
        mr.status = MATCH_REQUEST_CHOICES[1][0]  # ACCEPTED
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

        serializer = self.get_serializer(instance=mr)
        return Response(serializer.data, status.HTTP_200_OK)

    def reject(self, request: Request, match_request_id: int) -> Response:
        # Check validity
        mr = self.get_match_request_obj(match_request_id=match_request_id)
        self.is_user_receiver_group(match_request=mr)
        self.check_match_request_status(
            match_request=mr, target_status=MATCH_REQUEST_CHOICES[0][0]
        )  # WAITING

        mr.status = MATCH_REQUEST_CHOICES[2][0]  # REJECTED
        mr.save(update_fields=["status"])
        serializer = self.get_serializer(instance=mr)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def cancel(self, request: Request, match_request_id: int) -> Response:
        # Check validity
        mr = self.get_match_request_obj(match_request_id=match_request_id)
        self._is_user_sender_group(match_request=mr)
        self.check_match_request_status(
            match_request=mr, target_status=MATCH_REQUEST_CHOICES[0][0]
        )  # WAITING

        mr.status = MATCH_REQUEST_CHOICES[3][0]  # CANCELED
        mr.save(update_fields=["status"])
        serializer = self.get_serializer(instance=mr)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def get_match_request_obj(match_request_id: int) -> MatchRequest:
        try:
            mr = MatchRequest.objects.get(id=match_request_id)
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


# LEGACY
# ============================


class MatchRequestSentViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsUserJoinedGroupActive,
    ]
    serializer_class = MatchRequestSentSerializer

    def get_queryset(self) -> QuerySet:
        return MatchRequest.objects.filter(
            sender=self.request.user.joined_group, accepted=False, denied=False
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status.HTTP_200_OK)


class MatchRequestReceivedViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsUserJoinedGroupActive,
    ]
    serializer_class = MatchRequestReceivedSerializer

    def get_queryset(self) -> QuerySet:
        return MatchRequest.objects.filter(
            receiver=self.request.user.joined_group, accepted=False, denied=False
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status.HTTP_200_OK)


class MatchRequestControlViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsUserJoinedGroupActive,
    ]
    serializer_class = MatchRequestDetailSerializer

    @swagger_auto_schema(request_body=MatchRequestSendBodySerializer)
    def send(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        to_group = get_object_or_404(Group, id=self.kwargs["group_id"])
        qs: QuerySet = MatchRequest.objects.filter(
            receiver=to_group, sender=request.user.joined_group
        )
        if qs.exists():
            return Response(
                "You already sent request to the Group",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        mr = MatchRequest.objects.create(
            sender=self.request.user.joined_group,
            receiver=to_group,
        )
        serializer = self.get_serializer(mr)
        return Response(serializer.data, status.HTTP_200_OK)

    @swagger_auto_schema(request_body=MatchRequestSendBodySerializer)
    def accept(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        from_group = get_object_or_404(Group, id=self.kwargs["group_id"])
        qs: QuerySet = MatchRequest.objects.filter(
            sender=from_group,
            receiver=request.user.joined_group,
            accepted=False,
            denied=False,
        )
        if not qs.exists():
            return Response(
                "You did not receive any request from the Group or you have already accepted.",
                status=status.HTTP_401_UNAUTHORIZED,
            )
        mr: MatchRequest = qs.first()
        mr.unread = False
        mr.accepted = True
        mr.denied = False
        mr.save(update_fields=["unread", "accepted", "denied"])

        # Create Stream channel for group leaders for both groups
        qs: QuerySet = User.active_objects.filter(
            joined_group=from_group, is_group_leader=True
        )
        if not qs.exists():
            return Response(
                "Group leader not exists on sender group",
                status=status.HTTP_404_NOT_FOUND,
            )

        sender_group_leader = qs.first()
        channel = stream.channel(
            settings.STREAM_CHAT_CHANNEL_TYPE,
            None,
            data=dict(
                members=[str(request.user.id), str(sender_group_leader.id)],
                created_by_id=str(request.user.id),
            ),
        )
        # Note: query method creates a channel
        res = channel.query()
        serializer = self.get_serializer(
            mr,
            context={
                "stream_channel_info": {
                    "id": res["channel"]["id"],
                    "cid": res["channel"]["cid"],
                    "type": res["channel"]["type"],
                }
            },
        )
        # Save StreamChannel
        sc_active_until = (
            from_group.active_until
            if from_group.active_until < request.user.joined_group.active_until
            else request.user.joined_group.active_until
        )
        StreamChannel.objects.create(
            cid=res["channel"]["cid"], active_until=sc_active_until
        )

        # TODO: send push notification
        return Response(serializer.data, status.HTTP_200_OK)

    def deny(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        from_group = get_object_or_404(Group, id=self.kwargs["group_id"])
        qs: QuerySet = MatchRequest.objects.filter(
            sender=from_group,
            receiver=request.user.joined_group,
            accepted=False,
            denied=False,
        )
        if not qs.exists():
            return Response(
                "You did not receive any request from the Group or you have already denied.",
                status=status.HTTP_401_UNAUTHORIZED,
            )
        mr: MatchRequest = qs.first()
        mr.unread = False
        mr.accepted = False
        mr.denied = True
        mr.save(update_fields=["unread", "accepted", "denied"])

        # Add to BlackList
        GroupBlackList.objects.create(
            group=request.user.joined_group, blocked_group=from_group
        )

        serializer = self.get_serializer(mr)
        return Response(serializer.data, status.HTTP_200_OK)


class GroupStreamChatExitViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsUserJoinedGroupActive,
    ]

    def exit(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        from_group = get_object_or_404(Group, id=self.kwargs["group_id"])
        qs: QuerySet = MatchRequest.objects.filter(
            sender=from_group,
            receiver=request.user.joined_group,
            accepted=True,
            denied=False,
        )
        if not qs.exists():
            return Response(
                "MatchRequest does not exist. Should be already exited or not accepted MR.",
                status=status.HTTP_404_NOT_FOUND,
            )
        mr: MatchRequest = qs.first()
        mr.unread = False
        mr.accepted = False
        mr.denied = True
        mr.save(update_fields=["unread", "accepted", "denied"])

        # Add to BlackList
        GroupBlackList.objects.create(
            group=request.user.joined_group, blocked_group=from_group
        )

        # Delete Stream channel
        qs: QuerySet = User.active_objects.filter(
            joined_group=from_group, is_group_leader=True
        )
        if not qs.exists():
            return Response(
                "Group leader not exists on requested group",
                status=status.HTTP_404_NOT_FOUND,
            )

        sender_group_leader = qs.first()
        channel = stream.channel(
            settings.STREAM_CHAT_CHANNEL_TYPE,
            None,
            data=dict(
                members=[str(request.user.id), str(sender_group_leader.id)],
                created_by_id=str(request.user.id),
            ),
        )
        # Note: query method creates a channel
        res = channel.query()
        stream.delete_channels([res["channel"]["cid"]])

        # Mark StreamChannel inactive
        sc = StreamChannel.objects.get(cid=res["channel"]["cid"])
        sc.is_active = False
        sc.save(update_fields=["is_active"])
        return Response(status.HTTP_200_OK)


class MatchedGroupLeaderDetailViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsUserJoinedGroupActive,
    ]
    serializer_class = MatchedGroupLeaderDetailSerializer

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        other_group = get_object_or_404(Group, id=self.kwargs["group_id"])
        joined_group = request.user.joined_group

        qs1 = MatchRequest.objects.filter(sender=joined_group, receiver=other_group)
        qs2 = MatchRequest.objects.filter(sender=other_group, receiver=joined_group)

        if not (qs1.exists() or qs2.exists()):
            return Response(
                "You are not matched with the group.",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        qs: QuerySet = User.active_objects.filter(
            joined_group=other_group, is_group_leader=True
        )
        if not qs.exists():
            return Response("Group leader not exists", status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance=qs.first())
        return Response(serializer.data, status.HTTP_200_OK)
