from typing import Any

from drf_yasg.utils import swagger_auto_schema
from phone_verify.base import response
from phone_verify.serializers import PhoneSerializer
from phone_verify.services import send_security_code_and_generate_session_token
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class CustomUserRateThrottle(UserRateThrottle):
    rate = "10/min"


class CustomAnonRateThrottle(AnonRateThrottle):
    rate = "10/min"


class PhoneRegistrationViewSet(viewsets.ViewSet):
    throttle_classes = [
        CustomUserRateThrottle,
        CustomAnonRateThrottle,
    ]
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
