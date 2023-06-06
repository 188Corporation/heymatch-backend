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
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from heymatch.apps.user.models import EmailVerificationCode, User
from heymatch.shared.exceptions import (
    EmailVerificationCodeExpiredException,
    EmailVerificationCodeIncorrectException,
    EmailVerificationDomainNotFoundException,
    EmailVerificationSelectedNameNotFoundException,
)
from heymatch.utils.util import load_company_domain_file, load_school_domain_file

from .serializers import (
    EmailVerificationAuthCodeSerializer,
    EmailVerificationSendCodeSerializer,
)

COMPANY_DOMAIN_FILE = load_company_domain_file()
SCHOOL_DOMAIN_FILE = load_school_domain_file()


class PhoneUserRateThrottle(UserRateThrottle):
    rate = "10/min"


class PhoneAnonRateThrottle(AnonRateThrottle):
    rate = "10/min"


class EmailUserRateThrottle(UserRateThrottle):
    rate = "30/min"


class EmailAnonRateThrottle(AnonRateThrottle):
    rate = "30/min"


class PhoneRegistrationViewSet(viewsets.ViewSet):
    throttle_classes = [
        PhoneUserRateThrottle,
        PhoneAnonRateThrottle,
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
        EmailUserRateThrottle,
        EmailAnonRateThrottle,
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
        # Everything is good.
        # Update user.verified_company_name or verified_school_name
        found, names = self.determine_school_company_name_by_email(evc)
        if not found:
            raise EmailVerificationDomainNotFoundException()

        return Response(
            data={
                "type": evc.type,
                "names": names,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(request_body=EmailVerificationAuthCodeSerializer)
    def authorize(self, request: Request, *args: Any, **kwargs: Any):
        serializer = EmailVerificationAuthCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        evc_qs = EmailVerificationCode.active_objects.filter(
            user=request.user,
            email=serializer.validated_data["email"],
            type=serializer.validated_data["type"],
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

        found, names = self.determine_school_company_name_by_email(evc)
        selected_name = serializer.validated_data["selected_name"]
        if not found:
            raise EmailVerificationDomainNotFoundException()
        if selected_name not in names:
            raise EmailVerificationSelectedNameNotFoundException()

        # update user
        user = request.user
        if evc.type == EmailVerificationCode.VerificationType.SCHOOL:
            user.job_title = User.JobChoices.COLLEGE_STUDENT
            user.verified_school_name = selected_name
            user.save(update_fields=["job_title", "verified_school_name"])
        elif evc.type == EmailVerificationCode.VerificationType.COMPANY:
            user.job_title = User.JobChoices.EMPLOYEE
            user.verified_company_name = selected_name
            user.save(update_fields=["job_title", "verified_company_name"])

        # inactivate code
        evc.is_active = False
        evc.save(update_fields=["is_active"])
        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def determine_school_company_name_by_email(evc: EmailVerificationCode):
        # handle school
        email = evc.email
        email_domain = email.split("@")[1]
        if evc.type == EmailVerificationCode.VerificationType.SCHOOL:
            if email_domain in SCHOOL_DOMAIN_FILE:
                return True, SCHOOL_DOMAIN_FILE[email_domain]
            else:
                return False, None

        # handle company
        if evc.type == EmailVerificationCode.VerificationType.COMPANY:
            if email_domain in COMPANY_DOMAIN_FILE:
                return True, COMPANY_DOMAIN_FILE[email_domain]
        return False, None
