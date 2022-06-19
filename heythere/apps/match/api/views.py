from typing import Any

from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heythere.apps.group.models import Group
from heythere.apps.match.models import MatchRequest
from heythere.apps.user.models import User
from heythere.shared.permissions import (
    IsUserActive,
    IsUserGroupLeader,
    IsUserJoinedGroupActive,
)

from .serializers import (
    MatchedGroupLeaderDetailSerializer,
    MatchRequestAcceptSerializer,
    MatchRequestDetailSerializer,
    MatchRequestReceivedSerializer,
    MatchRequestSendBodySerializer,
    MatchRequestSentSerializer,
)

stream = settings.STREAM_CLIENT


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
        serializer = self.get_serializer(mr)
        return Response(serializer.data, status.HTTP_200_OK)


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
