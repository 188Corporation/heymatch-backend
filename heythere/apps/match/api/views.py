from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heythere.apps.group.models import Group
from heythere.apps.match.models import MatchRequest
from heythere.shared.permissions import (
    IsUserActive,
    IsUserGroupLeader,
    IsUserJoinedGroupActive,
)

from .serializers import (
    MatchRequestControlSerializer,
    MatchRequestReceivedDetailSerializer,
    MatchRequestReceivedListSerializer,
    MatchRequestSendBodySerializer,
    MatchRequestSentDetailSerializer,
    MatchRequestSentListSerializer,
)


class MatchRequestSentViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsUserJoinedGroupActive,
    ]

    def get_queryset(self) -> QuerySet:
        return MatchRequest.objects.filter(sender=self.request.user.joined_group)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = self.get_queryset()
        serializer = MatchRequestSentListSerializer(qs, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        mr = get_object_or_404(MatchRequest, uuid=self.kwargs["request_uuid"])
        serializer = MatchRequestSentDetailSerializer(instance=mr)
        return Response(serializer.data, status.HTTP_200_OK)


class MatchRequestReceivedViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsUserJoinedGroupActive,
    ]

    def get_queryset(self) -> QuerySet:
        return MatchRequest.objects.filter(receiver=self.request.user.joined_group)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = self.get_queryset()
        serializer = MatchRequestReceivedListSerializer(qs, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        mr = get_object_or_404(MatchRequest, uuid=self.kwargs["request_uuid"])
        serializer = MatchRequestReceivedDetailSerializer(instance=mr)
        return Response(serializer.data, status.HTTP_200_OK)


class MatchRequestControlViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsUserJoinedGroupActive,
    ]

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
            title=self.request.data["title"],
            content=self.request.data["content"],
        )
        serializer = MatchRequestControlSerializer(instance=mr)
        return Response(serializer.data, status.HTTP_200_OK)

    def accept(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        from_group = get_object_or_404(Group, id=self.kwargs["group_id"])
        qs: QuerySet = MatchRequest.objects.filter(
            sender=from_group, receiver=request.user.joined_group, accepted=False
        )
        if not qs.exists():
            return Response(
                "You did not receive any request from the Group or you have already accepted.",
                status=status.HTTP_401_UNAUTHORIZED,
            )
        mr: MatchRequest = qs.first()
        mr.unread = False
        mr.accepted = True
        mr.save(update_fields=["unread", "accepted"])
        serializer = MatchRequestControlSerializer(instance=mr)
        return Response(serializer.data, status.HTTP_200_OK)
