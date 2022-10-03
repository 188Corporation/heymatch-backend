from typing import Any

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import Group, GroupInvitationCode, GroupProfileImage
from heymatch.apps.hotplace.models import HotPlace
from heymatch.shared.exceptions import UserGPSNotWithinHotplaceException
from heymatch.shared.permissions import (
    IsGroupCreationAllowed,
    IsGroupRegisterAllowed,
    IsUserActive,
    IsUserJoinedGroup,
    IsUserNotGroupLeader,
)

from .serializers import (
    GroupFullInfoSerializer,
    GroupInvitationCodeCreateBodySerializer,
    GroupInvitationCodeSerializer,
    GroupRegisterConfirmationSerializer,
    GroupRegisterStep1BodySerializer,
    GroupRegisterStep1Serializer,
    GroupRegisterStep2BodySerializer,
    GroupRegisterStep2Serializer,
    GroupRegisterStep3PhotoUpdateSerializer,
    GroupRegisterStep3PhotoUploadSerializer,
    GroupRegisterStep3UpdatePhotoBodySerializer,
    GroupRegisterStep3UploadPhotoBodySerializer,
    GroupRegisterStep4Serializer,
    GroupWithBlurredProfileSortedByHotplaceSerializer,
    GroupWithOriginalProfileSortedByHotplaceSerializer,
)

User = get_user_model()


class GroupListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for searching, listing Groups
    """

    serializer_class = GroupWithBlurredProfileSortedByHotplaceSerializer
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
    ]

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = HotPlace.objects.prefetch_related("groups")

        # automatically checks if user joined group
        # if joined group, will give out original profile photo of groups in the hotplace
        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.request.user.joined_group:
            return GroupWithOriginalProfileSortedByHotplaceSerializer
        return self.serializer_class

    def get_serializer_context(self):
        context = super(GroupListViewSet, self).get_serializer_context()
        if self.request.user.joined_group:
            context.update({"hotplace_id": self.request.user.joined_group.hotplace.id})
        return context


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
            raise UserGPSNotWithinHotplaceException(
                detail="User's joined group should be in the same hotplace of the requested group."
            )
        serializer = GroupFullInfoSerializer(group)
        return Response(serializer.data)


class GroupCreateViewSet(viewsets.ModelViewSet):
    serializer_class = ""
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsGroupCreationAllowed,
    ]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return


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
    def validate_gps(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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
        - Need to enter invitation code. Code should be generated from member's heymatch app.
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsGroupRegisterAllowed,
    ]

    @swagger_auto_schema(request_body=GroupRegisterStep2BodySerializer)
    def invite_member(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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
    serializer_class = GroupRegisterStep3PhotoUploadSerializer
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsGroupRegisterAllowed,
    ]
    parser_classes = (MultiPartParser,)

    def get_serializer_class(self):
        if self.action == "update_photo":
            return GroupRegisterStep3PhotoUpdateSerializer
        return self.serializer_class

    @swagger_auto_schema(request_body=GroupRegisterStep3UploadPhotoBodySerializer)
    def upload_photo(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        from django.core.files.uploadedfile import InMemoryUploadedFile

        group = self.request.user.joined_group
        image: InMemoryUploadedFile = self.request.FILES.get("image")
        serializer.save(
            group=group,
            image=image,
        )
        group.register_step_3_completed = True
        group.save(update_fields=["register_step_3_completed"])

    @swagger_auto_schema(request_body=GroupRegisterStep3UpdatePhotoBodySerializer)
    def update_photo(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset, id=request.data["photo_id"], group=request.user.joined_group
        )
        # link image
        if self.request.FILES.get("image"):
            self.request.data["image"] = self.request.FILES.get("image")

        # serialize and update
        serializer = self.get_serializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GroupRegisterStep4ViewSet(viewsets.ModelViewSet):
    """
    4 of 4 Steps in Group Registration.

    * Step4: Basic Information Registration.
        - This will populate Group model fields.
    """

    queryset = Group.objects.all()
    serializer_class = GroupRegisterStep4Serializer
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsGroupRegisterAllowed,
    ]

    def write_profile(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        group = request.user.joined_group
        serializer = self.get_serializer(group, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        group.register_step_4_completed = True
        group.save(update_fields=["register_step_4_completed"])
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        IsGroupRegisterAllowed,
    ]

    def confirm(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Should confirm "gps_last_check_time", "steps_status"
        Should set "active_until"
        """
        # Being able to call below code means it passed Permission.
        # Set Group as active
        group = request.user.joined_group
        group.register_step_all_confirmed = True
        group.is_active = True
        group.save(update_fields=["register_step_all_confirmed", "is_active"])
        return Response("Group registered.", status=status.HTTP_200_OK)


class GroupUnregisterViewSet(viewsets.ViewSet):
    """
    Un-registration of Group ViewSet.
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsGroupRegisterAllowed,
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
