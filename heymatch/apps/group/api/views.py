from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django_google_maps.fields import GeoPt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import Group, ReportedGroup
from heymatch.apps.hotplace.models import HotPlace
from heymatch.apps.match.models import MatchRequest
from heymatch.shared.exceptions import (
    GroupNotWithinSameHotplaceException,
    JoinedGroupNotMineException,
    UserGPSNotWithinHotplaceException,
)
from heymatch.shared.permissions import (
    IsGroupCreationAllowed,
    IsUserActive,
    IsUserJoinedGroup,
)
from heymatch.utils.util import is_geopt_within_boundary

from .serializers import (
    FullGroupProfileByHotplaceSerializer,
    FullGroupProfileSerializer,
    GroupCreationRequestBodySerializer,
    GroupCreationSerializer,
    GroupUpdateSerializer,
    ReportGroupRequestBodySerializer,
    ReportGroupSerializer,
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
        MatchRequest.active_objects.filter(sender_group=group).update(is_active=False)
        MatchRequest.active_objects.filter(receiver_group=group).update(is_active=False)

        # Note: Stream chat will not be deleted. User should exit chat room explicitly from chat tab
        #  Thus, even though group is deleted, chat will still appear.
        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=GroupUpdateSerializer)
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        queryset = Group.active_objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        if user.joined_group.id != group.id:
            raise JoinedGroupNotMineException()

        gps_geoinfo = request.data.get("gps_geoinfo", group.gps_geoinfo)
        # validate gps
        try:
            gpt = GeoPt(gps_geoinfo)
        except ValidationError:
            raise UserGPSNotWithinHotplaceException()

        if not is_geopt_within_boundary(gpt, group.hotplace.zone_boundary_geoinfos):
            raise UserGPSNotWithinHotplaceException()

        group.gps_geoinfo = gps_geoinfo
        group.title = request.data.get("title", group.title)
        group.introduction = request.data.get("introduction", group.introduction)

        group.save(update_fields=["gps_geoinfo", "title", "introduction"])
        serializer = GroupUpdateSerializer(group)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class GroupReportViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserJoinedGroup,
    ]
    serializer_class = ReportGroupSerializer

    @swagger_auto_schema(request_body=ReportGroupRequestBodySerializer)
    def report(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        queryset = Group.active_objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])
        reported_reason = request.data.get("reported_reason", "")

        rg = ReportedGroup.objects.create(
            reported_group=group,
            reported_reason=reported_reason,
            reported_by=user,
        )
        serializer = self.get_serializer(rg)

        # Notify via slack
        slack_webhook = settings.SLACK_REPORT_GROUP_BOT
        slack_webhook.send(
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🚨*그룹 신고가 들어왔어요!*🚨"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "당직인 분은 당장 Django Admin에서 확인 후 조치를 취하세요!",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• *Environment*: {str(settings.DJANGO_ENV).upper()} \n "
                        f"• *신고한 유저 ID*: {str(request.user.id)} \n "
                        f"• *신고된 그룹 ID*: {str(kwargs['group_id'])} \n"
                        f"• *신고한 이유는?*: {str(reported_reason)}",
                    },
                },
            ]
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)
