from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from heythere.apps.search.models import HotPlace

from .serializers import HotPlaceDetailSerializer, HotPlaceListSerializer


class HotPlaceViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving HotPlaces.
    """

    def list(self, request):
        queryset = HotPlace.objects.all()
        serializer = HotPlaceListSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, id=None):
        queryset = HotPlace.objects.all()
        hotplace = get_object_or_404(queryset, id=id)
        serializer = HotPlaceDetailSerializer(hotplace)
        return Response(serializer.data)
