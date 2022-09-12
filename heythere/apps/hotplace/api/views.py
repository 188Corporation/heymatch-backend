from typing import Any

from django.db.models import Q
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heythere.apps.group.models import Group, GroupBlackList
from heythere.apps.hotplace.models import HotPlace

from .serializers import HotPlaceDetailSerializer, HotPlaceGroupSummarySerializer


class HotPlaceViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving HotPlaces.
    """

    permission_classes = [IsAuthenticated]

    def list(self, request) -> Response:
        queryset = HotPlace.objects.all()
        serializer = HotPlaceDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, hotplace_id: int) -> Response:
        queryset = HotPlace.objects.all()
        hotplace = get_object_or_404(queryset, id=hotplace_id)
        serializer = HotPlaceDetailSerializer(hotplace)
        return Response(serializer.data)


class HotPlaceActiveGroupViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing Active Groups in Hotplace
    """

    queryset = Group.active_objects.all()  # active by default
    serializer_class = HotPlaceGroupSummarySerializer
    # TODO: Only GPS authenticated Group users can see
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = self.queryset
        qs = qs.filter(hotplace_id=self.kwargs["hotplace_id"])
        joined_group = self.request.user.joined_group
        exclude_ids = []
        if joined_group:
            # Exclude myself
            exclude_ids.append(joined_group.id)
            # Exclude Blacklist
            blacklist_qs = GroupBlackList.active_objects.filter(group=joined_group)
            blocked_groups_ids = [bl.blocked_group.id for bl in blacklist_qs]
            exclude_ids.extend(blocked_groups_ids)
        qs = qs.filter(~Q(id__in=exclude_ids))
        return qs

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = self.get_queryset()
        qs = qs.filter(id=self.kwargs["group_id"])
        if qs.exists() and qs.count() == 1:
            serializer = self.get_serializer(qs.first())
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            data={"detail": "No matching groups found in the hotplace"},
            status=status.HTTP_404_NOT_FOUND,
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
