from typing import Any

from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from phone_verify.base import response
from phone_verify.serializers import PhoneSerializer
from phone_verify.services import send_security_code_and_generate_session_token
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heythere.shared.permissions import IsUserActive

stream = settings.STREAM_CLIENT


class StreamTokenViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for retrieving Token for GetStream User.
    """

    permission_classes = [IsAuthenticated & IsUserActive]

    def retrieve(self, request) -> Response:
        token = stream.create_token(user_id=str(self.request.user.id))
        return Response({"token": token})


class PhoneRegistrationViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = PhoneSerializer

    @swagger_auto_schema(request_body=PhoneSerializer)
    def register(self, request: Request, *args: Any, **kwargs: Any):
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_token = send_security_code_and_generate_session_token(
            str(serializer.validated_data["phone_number"])
        )
        return response.Ok({"session_token": session_token})
