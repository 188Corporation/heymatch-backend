from typing import Any

from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import Group, GroupBlackList
from heymatch.apps.match.models import MatchRequest, StreamChannel
from heymatch.apps.user.models import User
from heymatch.shared.permissions import (
    IsUserActive,
    IsUserGroupLeader,
    IsUserJoinedGroup,
    IsUserJoinedGroupActive,
)

from .serializers import (
    MatchedGroupLeaderDetailSerializer,
    MatchRequestAcceptSerializer,
    MatchRequestDetailSerializer,
    MatchRequestReceivedSerializer,
    MatchRequestSendBodySerializer,
    MatchRequestSentSerializer,
    MatchRequestSerializer,
)

stream = settings.STREAM_CLIENT


class MatchRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserJoinedGroup,
    ]
    serializer_class = MatchRequestSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # Query MatchRequest (newest to oldest)
        joined_group_id = self.request.user.joined_group.id
        mr_sent_qs = (
            MatchRequest.objects.select_related()
            .filter(sender_group_id=joined_group_id)
            .order_by("-created_at")
        )
        mr_received_qs = (
            MatchRequest.objects.select_related()
            .filter(receiver_group_id=joined_group_id)
            .order_by("-created_at")
        )

        # Serialize
        mr_sent_serializer = self.get_serializer(mr_sent_qs, many=True)
        mr_received_serializer = self.get_serializer(mr_received_qs, many=True)
        data = {
            "sent": mr_sent_serializer.data,
            "received": mr_received_serializer.data,
        }
        return Response(data=data, status=status.HTTP_200_OK)


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

    def get_serializer_class(self):
        if self.action == "accept":
            return MatchRequestAcceptSerializer
        return self.serializer_class

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
