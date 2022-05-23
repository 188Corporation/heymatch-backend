from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heythere.apps.match.models import MatchRequest
from heythere.shared.permissions import (
    IsUserActive,
    IsUserGroupLeader,
    IsUserJoinedGroupActive,
)

from .serializers import (
    MatchRequestReceivedDetailSerializer,
    MatchRequestReceivedListSerializer,
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
