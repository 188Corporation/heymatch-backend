from typing import Any

from django.db.models.query import QuerySet
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from heythere.apps.group.models import Group

from .serializers import GpsAuthenticationForGroupSerializer


class GpsAuthenticationForGroupViewSet(viewsets.ModelViewSet):
    """
    GPS Authentication For Group ViewSet.

    This ViewSet and related API url will be reversed called by several APIs
    including Group Registration Step flow, Message to Other Group Check Step flow etc.

    We have made this GPS authentication service as a separate view in order to prevent each flow
    implement their own service.
    """

    queryset = Group.objects.all()
    serializer_class = GpsAuthenticationForGroupSerializer
    # TODO: Check group registration step status and accept/deny if any
    permission_classes = [AllowAny]

    def get_queryset(self) -> QuerySet:
        # TODO
        qs = self.queryset
        qs = qs.filter(hotplace_id=self.kwargs["hotplace_id"])
        return qs

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # TODO
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
        # TODO
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # TODO
        return
