from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.user.models import AppInfo, DeleteScheduledUser, UserProfileImage
from heymatch.shared.exceptions import UserMainProfileImageNotFound
from heymatch.shared.permissions import IsUserActive

from .serializers import (
    AppInfoSerializer,
    DeleteScheduledUserRequestBodySerializer,
    DeleteScheduledUserSerializer,
    UserInfoUpdateBodyRequestSerializer,
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

    @never_cache
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = get_object_or_404(User, id=self.request.user.id)
        app_info = AppInfo.objects.all().first()
        user_info_serializer = self.get_serializer(
            instance=user, context={"force_original": True}
        )
        app_info_serializer = AppInfoSerializer(instance=app_info)
        data = {**user_info_serializer.data, "app_info": app_info_serializer.data}
        return Response(data, status.HTTP_200_OK)

    @swagger_auto_schema(request_body=UserInfoUpdateBodyRequestSerializer)
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = UserInfoUpdateBodyRequestSerializer(
            request.user, data=request.data
        )
        serializer.is_valid(raise_exception=True)

        # when it is first time signup
        if request.user.is_first_signup:
            # process main profile image
            main_profile_image: InMemoryUploadedFile = serializer.validated_data.pop(
                "main_profile_image", None
            )
            if not main_profile_image:
                if not UserProfileImage.active_objects.filter(is_main=True).exists():
                    raise UserMainProfileImageNotFound()
                else:
                    UserProfileImage.active_objects.create(
                        user=request.user, image=main_profile_image, is_main=True
                    )
            # process other profile image
            other_profile_image_1: InMemoryUploadedFile or None = (
                serializer.validated_data.pop("other_profile_image_1", None)
            )
            other_profile_image_2: InMemoryUploadedFile or None = (
                serializer.validated_data.pop("other_profile_image_2", None)
            )
            for other_img in [other_profile_image_1, other_profile_image_2]:
                if other_img:
                    UserProfileImage.active_objects.create(
                        user=request.user, image=other_img
                    )
            # mark is_first_signup=false
            serializer.validated_data["is_first_signup"] = False
        # normal update flow
        else:
            # TODO: WIP
            pass

        # user fields without image data
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
