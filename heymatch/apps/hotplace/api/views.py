from typing import Any

import geopy.distance
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import Group
from heymatch.apps.hotplace.models import HotPlace

from .serializers import (
    HotPlaceDetailSerializer,
    HotPlaceGroupSummarySerializer,
    HotPlaceNearestBodySerializer,
)


class HotPlaceViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving HotPlaces.
    """

    permission_classes = [
        # IsAuthenticated,
        # IsUserActive,
    ]

    def list(self, request) -> Response:
        queryset = HotPlace.active_objects.all()
        serializer = HotPlaceDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, hotplace_id: int) -> Response:
        queryset = HotPlace.active_objects.all()
        hotplace = get_object_or_404(queryset, id=hotplace_id)
        serializer = HotPlaceDetailSerializer(hotplace)
        return Response(serializer.data)


class HotPlaceNearestViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for retrieving HotPlaces that is nearest to the user.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=HotPlaceNearestBodySerializer)
    def nearest(self, request) -> Response:
        queryset = HotPlace.active_objects.all()
        hotplace = self.get_nearest_hotplace(
            request.data["lat"], request.data["long"], hotplace_qs=queryset
        )
        serializer = HotPlaceDetailSerializer(hotplace)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def get_nearest_hotplace(lat: str, long: str, hotplace_qs) -> HotPlace or None:
        nearest_hotplace = None
        nearest_meter = None
        for hp in hotplace_qs:
            hp_lat_lon = hp.zone_center_geoinfo
            dist_meter = geopy.distance.geodesic(
                (hp_lat_lon.lat, hp_lat_lon.lon), (lat, long)
            ).m
            if not nearest_hotplace:
                nearest_hotplace = hp
                nearest_meter = dist_meter
                continue
            if dist_meter < nearest_meter:
                nearest_hotplace = hp
                nearest_meter = dist_meter
        return nearest_hotplace


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
        # joined_group = self.request.user.joined_group
        # exclude_ids = []
        # if joined_group:
        #     # Exclude myself
        #     exclude_ids.append(joined_group.id)
        #     # Exclude Blacklist
        #     blacklist_qs = GroupBlackList.active_objects.filter(group=joined_group)
        #     blocked_groups_ids = [bl.blocked_group.id for bl in blacklist_qs]
        #     exclude_ids.extend(blocked_groups_ids)
        # qs = qs.filter(~Q(id__in=exclude_ids))
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
