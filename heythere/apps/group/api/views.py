from typing import Any

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heythere.apps.group.models import Group, GroupInvitationCode, GroupProfileImage

from .permissions import (
    IsGroupRegisterAllowed,
    IsUserActive,
    IsUserGroupLeader,
    IsUserNotGroupLeader,
)
from .serializers import (
    GroupInvitationCodeCreateBodySerializer,
    GroupInvitationCodeSerializer,
    GroupRegisterConfirmationSerializer,
    GroupRegisterStep1BodySerializer,
    GroupRegisterStep1Serializer,
    GroupRegisterStep2BodySerializer,
    GroupRegisterStep2Serializer,
    GroupRegisterStep3BodySerializer,
    GroupRegisterStep3Serializer,
    GroupRegisterStep4Serializer,
    UserJoinedGroupStatusSerializer,
)

User = get_user_model()


class GroupRegisterStatusViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
    ]  # TODO: User should be linked

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = get_object_or_404(User, id=self.request.user.id)
        serializer = UserJoinedGroupStatusSerializer(instance=user)
        return Response(serializer.data, status.HTTP_200_OK)


class GroupRegisterStep1ViewSet(viewsets.ModelViewSet):
    """
    1 of 4 Steps in Group Registration.

    * Step1: GPS authentication.
    """

    serializer_class = GroupRegisterStep1Serializer
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsGroupRegisterAllowed,
    ]

    @swagger_auto_schema(request_body=GroupRegisterStep1BodySerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GroupRegisterStep2ViewSet(viewsets.ViewSet):
    """
    2 of 4 Steps in Group Registration.

    * Step2: Member Invitation.
        - Need to enter invitation code. Code should be generated from member's Heythere app.
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsGroupRegisterAllowed,
    ]

    @swagger_auto_schema(request_body=GroupRegisterStep2BodySerializer)
    def invite(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = GroupRegisterStep2Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.perform_invite(serializer.validated_data, group_leader=request.user)
        return Response("All users invited successfully.", status=status.HTTP_200_OK)


class GroupRegisterStep3ViewSet(viewsets.ModelViewSet):
    """
    3 of 4 Steps in Group Registration.

    * Step3: Photo Registration.
        - Need to resize(thumbnail, original, resized) and store photo object to AWS S3.
    """

    queryset = GroupProfileImage.objects.all()
    serializer_class = GroupRegisterStep3Serializer
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsGroupRegisterAllowed,
    ]
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(request_body=GroupRegisterStep3BodySerializer)
    def upload(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(
            group=self.request.user.joined_group, image=self.request.FILES.get("image")
        )

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        pass


class GroupRegisterStep4ViewSet(viewsets.ModelViewSet):
    """
    4 of 4 Steps in Group Registration.

    * Step4: Basic Information Registration.
        - This will populate Group model fields.
    """

    serializer_class = GroupRegisterStep4Serializer
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsGroupRegisterAllowed,
    ]

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        pass


class GroupRegisterConfirmationViewSet(viewsets.ModelViewSet):
    """
    Confirmation step (=last step) in Group Registration.

    * Confirmation of Registration
        - This will confirm and validate all the required info before actually handling DB.
    """

    serializer_class = GroupRegisterConfirmationSerializer
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
        IsGroupRegisterAllowed,
    ]

    def confirm(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Should confirm "gps_last_check_time", "steps_status"
        Should set "active_until"
        """
        return Response()


class GroupUnregisterViewSet(viewsets.ViewSet):
    """
    Un-registration of Group ViewSet.
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserGroupLeader,
    ]

    def unregister(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # fetch joined group
        user: User = get_object_or_404(User, id=self.request.user.id)
        group: Group = user.joined_group
        Group.objects.unregister_all_users(group=group)
        return Response(status=status.HTTP_200_OK)


class GroupInvitationCodeViewSet(viewsets.ModelViewSet):
    """
    Generate Group Invitation Code.
    Should be called by none group_leader User.
    """

    queryset = GroupInvitationCode.active_objects.all()
    serializer_class = GroupInvitationCodeSerializer
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserNotGroupLeader,
    ]

    @swagger_auto_schema(request_body=GroupInvitationCodeCreateBodySerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # set previous codes as "used"
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
