from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.user.models import AppInfo, DeleteScheduledUser
from heymatch.shared.exceptions import UserAlreadyScheduledDeletionException

from .serializers import (
    AppInfoSerializer,
    DeleteScheduledUserSerializer,
    UserWithGroupFullInfoSerializer,
)

User = get_user_model()
stream = settings.STREAM_CLIENT


class UserWithGroupFullInfoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = get_object_or_404(User, id=self.request.user.id)
        app_info = AppInfo.objects.all().first()
        user_info_serializer = UserWithGroupFullInfoSerializer(
            instance=user, context={"force_original": True}
        )
        app_info_serializer = AppInfoSerializer(instance=app_info)
        data = {**user_info_serializer.data, "app_info": app_info_serializer.data}
        return Response(data, status.HTTP_200_OK)

    def schedule_delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # NOTE: jwt token must be deleted client side
        # create DeleteScheduledUser
        user = request.user
        try:
            dsu = DeleteScheduledUser.objects.create(user=user)
        except IntegrityError:
            raise UserAlreadyScheduledDeletionException()

        serializer = DeleteScheduledUserSerializer(instance=dsu)

        # rest of job will be done by celery-beat scheduler
        return Response(data=serializer.data, status=status.HTTP_200_OK)
