from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import Group
from heymatch.apps.hotplace.models import HotPlace
from heymatch.apps.match.models import MatchRequest
from heymatch.shared.exceptions import (
    GroupNotWithinSameHotplaceException,
    JoinedGroupNotMineException,
)
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
stream = settings.STREAM_CLIENT


class GroupsGenericViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating Groups
    """

    parser_classes = [MultiPartParser]
    serializer_class = RestrictedGroupProfileByHotplaceSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = HotPlace.objects.prefetch_related(
            Prefetch("groups", queryset=Group.active_objects.all())
        )
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


class GroupDetailViewSet(viewsets.ModelViewSet):
    """
    ViewSet for detail view of Groups

    If user does not belong to any group, deny.
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserJoinedGroup,
    ]
    serializer_class = FullGroupProfileSerializer

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = Group.active_objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])
        if request.user.joined_group.hotplace.id != group.hotplace.id:
            raise GroupNotWithinSameHotplaceException()
        serializer = self.get_serializer(group)
        return Response(serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        queryset = Group.active_objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        if user.joined_group.id != group.id:
            raise JoinedGroupNotMineException()

        # Unlink from User
        user.joined_group = None
        user.save(update_fields=["joined_group"])

        # Deactivate Group
        group.is_active = False
        group.save(update_fields=["is_active"])

        # Deactivate MatchRequest
        sent_mrs = MatchRequest.active_objects.filter(sender_group=group)
        sent_mrs.is_active = False
        sent_mrs.save(update_fields=["is_active"])
        received_mrs = MatchRequest.active_objects.filter(receiver_group=group)
        received_mrs.is_active = False
        received_mrs.save(update_fields=["is_active"])

        # Deactivate Stream Chat
        channels = stream.query_channels(
            filter_conditions={
                "members": {"$in": [str(request.user.id)]},
                "disabled": False,
            }
        )
        for channel in channels["channels"]:
            ch = stream.channel(
                channel_type=channel["channel"]["type"],
                channel_id=channel["channel"]["id"],
            )
            ch.update_partial(to_set={"disabled": True})

        return Response(status=status.HTTP_200_OK)
