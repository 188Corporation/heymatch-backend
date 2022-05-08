from typing import Any

from django.db.models.query import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from heythere.apps.group.models import Group

from .serializers import (
    GroupRegisterStep1Serializer,
    GroupRegisterStep2Serializer,
    GroupRegisterStep3Serializer,
    GroupRegisterStep4Serializer,
)


class _GroupRegisterStepBaseViewSet(viewsets.ModelViewSet):
    """
    Base Group Registration. Step[1-4]ViewSet must inherit this class.
    """

    queryset = Group.objects.all()
    permission_classes = [AllowAny]  # TODO

    def get_queryset(self) -> QuerySet:
        qs = self.queryset
        return qs

    def check_step(self, request: Request, *args: Any, **kwargs: Any):
        """
        Check if step
        """

    def handle_step(self, request: Request, *args: Any, **kwargs: Any):
        pass


class GroupRegisterStep1ViewSet(_GroupRegisterStepBaseViewSet):
    """
    1 of 4 Steps in Group Registration.

    * Step1: GPS authentication.
        - This will reverse call to api/auth/gps/authenticate/group/{group_id}
    """

    serializer_class = GroupRegisterStep1Serializer

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # step_num = self.kwargs["step_num"]
        self.get_serializer()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # step_num = self.kwargs["step_num"]
        pass


class GroupRegisterStep2ViewSet(_GroupRegisterStepBaseViewSet):
    """
    2 of 4 Steps in Group Registration.

    * Step2: Photo Registration.
        - Need to resize(thumbnail, original, resized) and store photo object to AWS S3.
    """

    serializer_class = GroupRegisterStep2Serializer


class GroupRegisterStep3ViewSet(_GroupRegisterStepBaseViewSet):
    """
    3 of 4 Steps in Group Registration.

    * Step3: Basic Information Registration.
        - This will populate Group model fields.
    """

    serializer_class = GroupRegisterStep3Serializer


class GroupRegisterStep4ViewSet(_GroupRegisterStepBaseViewSet):
    """
    4 of 4 Steps in Group Registration.

    * Step4: Confirmation of Registration
        - This will confirm and validate all the required info before actually handling DB.
    """

    serializer_class = GroupRegisterStep4Serializer
