from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseServerError
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.user.models import DeleteScheduledUser
from heymatch.shared.permissions import IsUserActive

from .serializers import DeleteScheduledUserSerializer

User = get_user_model()
stream = settings.STREAM_CLIENT


class UserWithGroupFullInfoViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
    ]

    def retrieve(self, request: Request, *args: Any, **kwargs: Any):
        # user = get_object_or_404(User, id=self.request.user.id)
        # app_info = AppInfo.objects.all().first()
        # user_info_serializer = UserWithGroupFullInfoSerializer(
        #     instance=user, context={"force_original": True}
        # )
        # app_info_serializer = AppInfoSerializer(instance=app_info)
        # data = {**user_info_serializer.data, "app_info": app_info_serializer.data}
        # return Response(data, status.HTTP_200_OK)
        return HttpResponseServerError()

    def schedule_delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # NOTE: jwt token must be deleted client side
        # Whether user is under scheduled deletion is checked in permission
        user = request.user
        dsu = DeleteScheduledUser.objects.create(user=user)
        serializer = DeleteScheduledUserSerializer(instance=dsu)

        # rest of job will be done by celery-beat scheduler
        return Response(data=serializer.data, status=status.HTTP_200_OK)
