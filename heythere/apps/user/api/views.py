from typing import Any

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import UserWithGroupFullInfoSerializer

User = get_user_model()


class UserWithGroupFullInfoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = get_object_or_404(User, id=self.request.user.id)
        serializer = UserWithGroupFullInfoSerializer(instance=user)
        return Response(serializer.data, status.HTTP_200_OK)
