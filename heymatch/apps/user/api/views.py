import base64
import hashlib
import math
import urllib
from typing import Any, Dict, Optional

import requests
from admob_ssv.conf import settings as admob_settings
from admob_ssv.signals import valid_admob_ssv
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.models import GroupMember
from heymatch.apps.user.models import (
    AppInfo,
    DeleteScheduledUser,
    UserInvitation,
    UserOnBoarding,
    UserProfileImage,
)
from heymatch.shared.exceptions import (
    UserInvitationCodeAlreadyAcceptedException,
    UserInvitationCodeNotExistException,
    UsernameAlreadyExistsException,
)
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
onesignal_client = settings.ONE_SIGNAL_CLIENT


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
                orig_other_profile_image_1.save(
                    update_fields=[
                        "image",
                        "image_blurred",
                        "thumbnail",
                        "thumbnail_blurred",
                    ]
                )
            else:
                orig_other_profile_image_1 = UserProfileImage.objects.create(
                    user=request.user,
                    image=new_other_profile_image_1,
                    status=UserProfileImage.StatusChoices.ACCEPTED,
                )

        if new_other_profile_image_2:
            if orig_other_profile_image_2:
                orig_other_profile_image_2.image = new_other_profile_image_2
                orig_other_profile_image_2.save(
                    update_fields=[
                        "image",
                        "image_blurred",
                        "thumbnail",
                        "thumbnail_blurred",
                    ]
                )
            else:
                orig_other_profile_image_2 = UserProfileImage.objects.create(
                    user=request.user,
                    image=new_other_profile_image_2,
                    status=UserProfileImage.StatusChoices.ACCEPTED,
                )
                orig_other_profile_image_2.below(orig_other_profile_image_1)

        # user should verify again when changing job title
        job_title = serializer.validated_data.get("job_title", None)
        if job_title and (job_title != request.user.job_title):
            request.user.verified_school_name = None
            request.user.verified_company_name = None
            request.user.save(
                update_fields=["verified_school_name", "verified_company_name"]
            )

        if "block_my_school_or_company_users" in serializer.validated_data.keys():
            request.user.block_my_school_or_company_users = serializer.validated_data[
                "block_my_school_or_company_users"
            ]
            request.user.save(update_fields=["block_my_school_or_company_users"])

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
        qs = UserProfileImage.objects.filter(
            user=request.user, is_main=False, is_active=True
        )

        orig_other_profile_image_1 = None
        orig_other_profile_image_2 = None
        for q in qs:
            if q.order == 0:
                orig_other_profile_image_1 = q
            if q.order == 1:
                orig_other_profile_image_2 = q
            else:
                break

        for target in to_delete:
            if target == "other_profile_image_1":
                if orig_other_profile_image_1:
                    orig_other_profile_image_1.delete()
            elif target == "other_profile_image_2":
                if orig_other_profile_image_2:
                    orig_other_profile_image_2.delete()
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


class UserInvitationCodeViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

    def accept(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        BONUS_POINT = 5
        invitation_code = kwargs["invitation_code"]
        qs = User.objects.filter(invitation_code=invitation_code)
        if not qs.exists():
            raise UserInvitationCodeNotExistException()
        sent = qs.first()
        received = request.user
        if UserInvitation.objects.filter(sent=sent, received=received).exists():
            raise UserInvitationCodeAlreadyAcceptedException()
        UserInvitation.objects.create(sent=sent, received=received)
        # add point to each
        sent.point_balance = sent.point_balance + BONUS_POINT
        sent.save(update_fields=["point_balance"])
        onesignal_client.send_notification_to_specific_users(
            title=f"[{str(received.username)}]님께서 초대를 수락했어요!",
            content=f"보너스 캔디 {BONUS_POINT}개를 얻으셨어요!!😵",
            user_ids=[str(sent.id)],
        )

        received.point_balance = received.point_balance + BONUS_POINT
        received.save(update_fields=["point_balance"])
        onesignal_client.send_notification_to_specific_users(
            title=f"[{str(sent.username)}]님의 초대를 수락했어요!",
            content=f"보너스 캔디 {BONUS_POINT}개를 얻으셨어요!!😵",
            user_ids=[str(received.id)],
        )
        return Response(status=status.HTTP_200_OK)


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
        if uob.onboarding_completed:
            # After first-signup process
            if uob.profile_photo_under_verification:
                return Response(
                    data={
                        "status": "onboarding_completed",
                        "extra": "profile_under_verification",
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                data={
                    "status": "onboarding_completed",
                },
                status=status.HTTP_200_OK,
            )
        if uob.profile_photo_rejected:
            return Response(
                data={
                    "status": "onboarding_profile_rejected",
                    "rejected_reason": uob.profile_photo_rejected_reason,
                },
                status=status.HTTP_200_OK,
            )
        if uob.profile_photo_under_verification:
            return Response(
                data={
                    "status": "onboarding_profile_under_verification",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            data={
                "status": "onboarding_incomplete",
            },
            status=status.HTTP_200_OK,
        )

    # @swagger_auto_schema(request_body=no_body)
    # def in_progress_extra_info(
    #     self, request: Request, *args: Any, **kwargs: Any
    # ) -> Response:
    #     uob = get_object_or_404(UserOnBoarding, user=request.user)
    #     uob.extra_info_in_progress = True
    #     uob.save(update_fields=["extra_info_in_progress"])
    #     return Response(
    #         data={"extra_info_in_progress": uob.extra_info_in_progress},
    #         status=status.HTTP_200_OK,
    #     )

    # @swagger_auto_schema(request_body=no_body)
    # def complete_extra_info(
    #     self, request: Request, *args: Any, **kwargs: Any
    # ) -> Response:
    #     uob = get_object_or_404(UserOnBoarding, user=request.user)
    #     uob.extra_info_in_progress = False
    #     uob.extra_info_completed = True
    #     uob.save(update_fields=["extra_info_in_progress", "extra_info_completed"])
    #     return Response(status=status.HTTP_200_OK)


class UsersAdmobSSVViewSet(viewsets.ViewSet):
    SIGNATURE_PARAM_NAME = "signature"
    KEY_ID_PARAM_NAME = "key_id"

    permission_classes = [AllowAny]

    def retrieve(self, request: HttpRequest) -> Response:
        if self.SIGNATURE_PARAM_NAME not in request.GET:
            return Response("Missing signature", status=status.HTTP_400_BAD_REQUEST)

        if self.KEY_ID_PARAM_NAME not in request.GET:
            return Response("Missing key_id", status=status.HTTP_400_BAD_REQUEST)

        key_id = request.GET[self.KEY_ID_PARAM_NAME]
        public_key = self.get_public_key(key_id)

        if public_key is None:
            return Response("Unknown key_id", status=status.HTTP_400_BAD_REQUEST)

        signature = self.get_signature(request)
        content = self.get_unverified_content(request)

        if self.verify_signature(public_key, signature, content):
            self.handle_valid_ssv(request)
            return Response(status=status.HTTP_200_OK)

        return Response("Invalid signature", status=status.HTTP_400_BAD_REQUEST)

    def get_signature(self, request: HttpRequest) -> bytes:
        encoded_signature = request.GET[self.SIGNATURE_PARAM_NAME]

        # Ensure that the signatures padding is always a multiple of 4. Note that
        # the decode function will ignore extraneous padding. Before the decode
        # method would occasionaly yield the following exception:
        # binascii.Error: Incorrect padding
        return base64.urlsafe_b64decode(encoded_signature + "===")

    def get_unverified_content(self, request: HttpRequest) -> bytes:
        # According to the Admob SSV documentation, the last two query
        # parameters of rewarded video SSV callbacks are always
        # signature and key_id, in that order. The remaining query
        # parameters specify the content to be verified.
        query_string = request.META["QUERY_STRING"]
        signature_start_index = query_string.index(f"&{self.SIGNATURE_PARAM_NAME}=")
        escaped_content = query_string[:signature_start_index]
        return urllib.parse.unquote(escaped_content).encode("utf-8")

    def get_public_key(self, key_id: str) -> Optional[str]:
        cached_public_keys = cache.get(admob_settings.keys_cache_key, default={})
        cached_public_key = cached_public_keys.get(key_id, None)

        if cached_public_key is not None:
            return cached_public_key

        fetched_public_keys = self.fetch_public_keys()
        cache.set(
            admob_settings.keys_cache_key,
            fetched_public_keys,
            math.floor(admob_settings.keys_cache_timeout.total_seconds()),
        )
        return fetched_public_keys.get(key_id, None)

    def fetch_public_keys(self) -> Dict[str, str]:
        response = requests.get(admob_settings.keys_server_url)
        response.raise_for_status()
        json_data = response.json()
        return {str(key["keyId"]): key["pem"] for key in json_data["keys"]}

    def verify_signature(
        self, public_key: str, signature: bytes, content: bytes
    ) -> bool:
        from ecdsa import BadSignatureError, VerifyingKey
        from ecdsa.util import sigdecode_der

        verifying_key = VerifyingKey.from_pem(public_key)

        try:
            return verifying_key.verify(
                signature,
                content,
                hashfunc=hashlib.sha256,
                sigdecode=sigdecode_der,
            )
        except BadSignatureError:
            return False

    def handle_valid_ssv(self, request: HttpRequest) -> None:
        valid_admob_ssv.send(sender=None, query=request.GET.dict())
