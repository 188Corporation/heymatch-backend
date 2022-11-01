from typing import Any

from drf_yasg.utils import swagger_auto_schema
from phone_verify.base import response
from phone_verify.serializers import PhoneSerializer
from phone_verify.services import send_security_code_and_generate_session_token
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request


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
