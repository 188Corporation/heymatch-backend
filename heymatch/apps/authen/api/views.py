from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from drf_yasg.utils import swagger_auto_schema
from phone_verify.base import response
from phone_verify.models import SMSVerification
from phone_verify.serializers import PhoneSerializer
from phone_verify.services import send_security_code_and_generate_session_token
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from heymatch.apps.user.models import EmailVerificationCode
from heymatch.shared.exceptions import (
    EmailVerificationCodeExpiredException,
    EmailVerificationCodeIncorrectException,
)

from .serializers import (
    EmailVerificationAuthCodeSerializer,
    EmailVerificationSendCodeSerializer,
)


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
        # Provide backdoor for App store review
        if request.data.get("phone_number", None) == settings.BACKDOOR_PHONE_NUMBER:
            self.create_sms_verification_for_backdoor(
                settings.BACKDOOR_PHONE_NUMBER,
                settings.BACKDOOR_SECURITY_CODE,
                settings.BACKDOOR_SESSION_TOKEN,
            )
            return response.Ok({"session_token": settings.BACKDOOR_SESSION_TOKEN})

        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_token = send_security_code_and_generate_session_token(
            str(serializer.validated_data["phone_number"])
        )
        return response.Ok({"session_token": session_token})

    @staticmethod
    def create_sms_verification_for_backdoor(
        number: str, security_code: str, session_token: str
    ):
        # Delete old security_code(s) for phone_number if already exists
        SMSVerification.objects.filter(phone_number=number).delete()
        SMSVerification.objects.create(
            phone_number=number,
            security_code=security_code,
            session_token=session_token,
            is_verified=True,
        )


class EmailVerificationViewSet(viewsets.ViewSet):
    throttle_classes = [
        CustomUserRateThrottle,
        CustomAnonRateThrottle,
    ]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=EmailVerificationSendCodeSerializer)
    def get_code(self, request: Request, *args: Any, **kwargs: Any):
        # Generate code
        serializer = EmailVerificationSendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Mark existing code as inactive
        qs = EmailVerificationCode.objects.filter(user=request.user)
        qs.update(is_active=False)

        # Create one
        evc = serializer.save(user=request.user)

        # Send mail
        subject = "[헤이매치] 이메일 인증 코드입니다"
        html_message = render_to_string(
            "email_verification_template.html",
            context={"verification_code": evc.code},
        )
        plain_message = strip_tags(html_message)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email="admin@hey-match.com",
            recipient_list=[evc.email],
            html_message=html_message,
            fail_silently=False,
        )
        return response.Ok()

    @swagger_auto_schema(request_body=EmailVerificationAuthCodeSerializer)
    def authorize(self, request: Request, *args: Any, **kwargs: Any):
        serializer = EmailVerificationAuthCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        evc_qs = EmailVerificationCode.active_objects.filter(
            user=request.user,
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
        )

        if not evc_qs.exists():
            raise EmailVerificationCodeIncorrectException()

        # Check active_until, if not mark it inactive
        evc = evc_qs.first()
        if evc.active_until < timezone.now():
            # Inactivate code
            evc.is_active = False
            evc.save(update_fields=["is_active"])
            raise EmailVerificationCodeExpiredException()

        # Everything is good.
        # Update user.verified_company_name or verified_school_name

        return response.Ok()
