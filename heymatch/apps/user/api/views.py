from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import get_object_or_404
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import GroupMember
from heymatch.apps.user.models import (
    AppInfo,
    DeleteScheduledUser,
    UserOnBoarding,
    UserProfileImage,
)
from heymatch.shared.exceptions import UsernameAlreadyExistsException
from heymatch.shared.permissions import IsUserActive

from .serializers import (
    AppInfoSerializer,
    DeleteScheduledUserRequestBodySerializer,
    DeleteScheduledUserSerializer,
    DeleteUserProfilePhotoRequestBodySerializer,
    GroupMemberSerializer,
    TempUserCreateSerializer,
    UserInfoUpdateBodyRequestSerializer,
    UsernameUniquenessCheckSerializer,
    UserProfileImageSerializer,
    UserWithGroupFullInfoSerializer,
)

User = get_user_model()
stream = settings.STREAM_CLIENT


class UserWithGroupFullInfoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
    ]
    parser_classes = [MultiPartParser]
    serializer_class = UserWithGroupFullInfoSerializer

    # @never_cache
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = get_object_or_404(User, id=self.request.user.id)
        app_info = AppInfo.objects.all().first()
        user_info_serializer = self.get_serializer(
            instance=user, context={"force_original": True}
        )
        qs = UserProfileImage.objects.filter(
            user=request.user, status=UserProfileImage.StatusChoices.ACCEPTED
        )
        user_profile_image_serializer = UserProfileImageSerializer(qs, many=True)

        gm_qs = GroupMember.objects.filter(user=request.user, is_active=True)
        gm_serializer = GroupMemberSerializer(gm_qs, many=True)
        app_info_serializer = AppInfoSerializer(instance=app_info)
        data = {
            **user_info_serializer.data,
            "user_profile_images": user_profile_image_serializer.data,
            "joined_groups": gm_serializer.data,
            "app_info": app_info_serializer.data,
        }
        return Response(data, status.HTTP_200_OK)

    @swagger_auto_schema(request_body=UserInfoUpdateBodyRequestSerializer)
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = UserInfoUpdateBodyRequestSerializer(
            request.user, data=request.data
        )
        serializer.is_valid(raise_exception=True)

        main_profile_image: InMemoryUploadedFile = serializer.validated_data.pop(
            "main_profile_image", None
        )
        if main_profile_image:
            # first create inactive photo
            # once accepted, will be changed to active
            UserProfileImage.all_objects.create(
                user=request.user,
                image=main_profile_image,
                is_main=True,
                status=UserProfileImage.StatusChoices.NOT_VERIFIED,
                is_active=False,  # first make it inactive
            )
            uob = UserOnBoarding.objects.get(user=request.user)
            # if user under onboarding
            if not uob.onboarding_completed:
                uob.profile_photo_under_verification = True
                uob.profile_photo_rejected = False
                uob.save(
                    update_fields=[
                        "profile_photo_under_verification",
                        "profile_photo_rejected",
                    ]
                )

        # process other profile image
        qs = UserProfileImage.objects.filter(user=request.user, is_main=False)
        if len(qs) == 2:
            orig_other_profile_image_1 = qs[0]
            orig_other_profile_image_2 = qs[1]
        elif len(qs) == 1:
            orig_other_profile_image_1 = qs[0]
            orig_other_profile_image_2 = None
        else:
            orig_other_profile_image_1 = None
            orig_other_profile_image_2 = None

        new_other_profile_image_1: InMemoryUploadedFile or None = (
            serializer.validated_data.pop("other_profile_image_1", None)
        )
        new_other_profile_image_2: InMemoryUploadedFile or None = (
            serializer.validated_data.pop("other_profile_image_2", None)
        )

        if new_other_profile_image_1:
            if orig_other_profile_image_1:
                orig_other_profile_image_1.image = new_other_profile_image_1
                orig_other_profile_image_1.save(update_fields=["image"])
            else:
                orig_other_profile_image_1 = UserProfileImage.objects.create(
                    user=request.user,
                    image=new_other_profile_image_1,
                    status=UserProfileImage.StatusChoices.ACCEPTED,
                )

        if new_other_profile_image_2:
            if orig_other_profile_image_2:
                orig_other_profile_image_2.image = new_other_profile_image_2
                orig_other_profile_image_2.save(update_fields=["image"])
            else:
                orig_other_profile_image_2 = UserProfileImage.objects.create(
                    user=request.user,
                    image=new_other_profile_image_2,
                    status=UserProfileImage.StatusChoices.ACCEPTED,
                )
                orig_other_profile_image_2.below(orig_other_profile_image_1)

        # user should verify again when changing job title
        if "job_title" in serializer.validated_data.keys():
            request.user.verified_school_name = None
            request.user.verified_company_name = None
            request.user.save(
                update_fields=["verified_school_name", "verified_company_name"]
            )

        serializer.save()
        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=DeleteScheduledUserRequestBodySerializer)
    def schedule_delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # NOTE: jwt token must be deleted client side
        # Whether user is under scheduled deletion is checked in permission
        user = request.user
        dsu = DeleteScheduledUser.objects.create(
            user=user, delete_reason=request.data.get("delete_reason", None)
        )
        serializer = DeleteScheduledUserSerializer(instance=dsu)

        # rest of job will be done by celery-beat scheduler
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserWithGroupProfilePhotoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        # IsUserActive,
    ]

    serializer_class = DeleteUserProfilePhotoRequestBodySerializer

    @swagger_auto_schema(request_body=DeleteUserProfilePhotoRequestBodySerializer)
    def delete_profile_photo(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        data = request.data["to_delete"]
        try:
            to_delete = str(data).split(",")
        except AttributeError:
            return Response(data="Invalid field", status=status.HTTP_400_BAD_REQUEST)
        qs = UserProfileImage.objects.filter(user=request.user, is_main=False)

        if len(qs) == 2:
            orig_other_profile_image_1 = qs[0]
            orig_other_profile_image_2 = qs[1]
        elif len(qs) == 1:
            orig_other_profile_image_1 = qs[0]
            orig_other_profile_image_2 = None
        else:
            orig_other_profile_image_1 = None
            orig_other_profile_image_2 = None

        for target in to_delete:
            if target == "other_profile_image_1":
                if orig_other_profile_image_1:
                    orig_other_profile_image_1.delete()
                    # orig_other_profile_image_1.is_active = False
                    # orig_other_profile_image_1.save(update_fields=["is_active"])
            elif target == "other_profile_image_2":
                if orig_other_profile_image_2:
                    orig_other_profile_image_2.delete()
                    # orig_other_profile_image_2.is_active = False
                    # orig_other_profile_image_2.save(update_fields=["is_active"])
            else:
                return Response(
                    data=f"Invalid field - {data}", status=status.HTTP_400_BAD_REQUEST
                )
        return Response(status=status.HTTP_200_OK)


class UsernameUniquenessCheckViewSet(viewsets.ModelViewSet):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = UsernameUniquenessCheckSerializer

    @swagger_auto_schema(request_body=UsernameUniquenessCheckSerializer)
    def check(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if User.objects.filter(username__iexact=request.data["username"]).exists():
            raise UsernameAlreadyExistsException()
        return Response(data="This username is good to go!", status=status.HTTP_200_OK)


class TempUserCreateViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
    ]
    serializer_class = TempUserCreateSerializer

    @swagger_auto_schema(request_body=TempUserCreateSerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer) -> None:
        serializer.save(is_temp_user=True)


class UserOnboardingViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        uob = get_object_or_404(UserOnBoarding, user=request.user)
        if uob.extra_info_in_progress:
            return Response(
                data={"status": "onboarding_extra_info_in_progress"},
                status=status.HTTP_200_OK,
            )
        if uob.onboarding_completed:
            if uob.profile_photo_under_verification:
                return Response(
                    data={
                        "status": "onboarding_completed",
                        "extra": "profile_under_verification",
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                data={"status": "onboarding_completed"}, status=status.HTTP_200_OK
            )
        if uob.profile_photo_rejected:
            return Response(
                data={"status": "onboarding_profile_rejected"},
                status=status.HTTP_200_OK,
            )
        if uob.profile_photo_under_verification:
            if uob.extra_info_completed:
                return Response(
                    data={
                        "status": "onboarding_profile_under_verification_extra_info_completed"
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    data={
                        "status": "onboarding_profile_under_verification_extra_info_incomplete"
                    },
                    status=status.HTTP_200_OK,
                )
        return Response(
            data={"status": "onboarding_basic_info_incomplete"},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(request_body=no_body)
    def in_progress_extra_info(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        uob = get_object_or_404(UserOnBoarding, user=request.user)
        uob.extra_info_in_progress = True
        uob.save(update_fields=["extra_info_in_progress"])
        return Response(
            data={"extra_info_in_progress": uob.extra_info_in_progress},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(request_body=no_body)
    def complete_extra_info(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        uob = get_object_or_404(UserOnBoarding, user=request.user)
        uob.extra_info_in_progress = False
        uob.extra_info_completed = True
        uob.save(update_fields=["extra_info_in_progress", "extra_info_completed"])
        return Response(status=status.HTTP_200_OK)
