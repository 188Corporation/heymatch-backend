from typing import Any

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import Group
from heymatch.apps.hotplace.models import HotPlace
from heymatch.shared.exceptions import GroupNotWithinSameHotplaceException
from heymatch.shared.permissions import (
    IsGroupCreationAllowed,
    IsUserActive,
    IsUserJoinedGroup,
)

from .serializers import (
    FullGroupProfileByHotplaceSerializer,
    FullGroupProfileSerializer,
    GroupCreationRequestBodySerializer,
    GroupCreationSerializer,
    RestrictedGroupProfileByHotplaceSerializer,
)

User = get_user_model()


class GroupsGenericViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating Groups
    """

    parser_classes = [MultiPartParser]
    serializer_class = RestrictedGroupProfileByHotplaceSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = HotPlace.objects.prefetch_related("groups")
        # Automatically checks if user joined group
        # if joined group, will give out original profile photo of groups in the hotplace
        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=GroupCreationRequestBodySerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
            IsUserActive,
        ]
        if self.request.method == "POST":
            permission_classes.append(IsGroupCreationAllowed)
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        context = super(GroupsGenericViewSet, self).get_serializer_context()
        if self.request.method == "POST":
            return context
        if (
            hasattr(self.request.user, "joined_group")
            and self.request.user.joined_group
        ):
            context.update({"hotplace_id": self.request.user.joined_group.hotplace.id})
        return context

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GroupCreationSerializer
        if (
            hasattr(self.request.user, "joined_group")
            and self.request.user.joined_group
        ):
            return FullGroupProfileByHotplaceSerializer
        return self.serializer_class

    def get_parsers(self):
        parsers = super(GroupsGenericViewSet, self).get_parsers()
        if self.request.method == "GET":
            parsers = [JSONParser]
        return parsers


class GroupDetailViewSet(viewsets.ViewSet):
    """
    ViewSet for detail view of Groups

    If user does not belong to any group, deny.
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserJoinedGroup,
    ]

    def retrieve(self, request, group_id: int) -> Response:
        queryset = Group.active_objects.all()
        group = get_object_or_404(queryset, id=group_id)
        if request.user.joined_group.hotplace.id != group.hotplace.id:
            raise GroupNotWithinSameHotplaceException()
        serializer = FullGroupProfileSerializer(group)
        return Response(serializer.data)
