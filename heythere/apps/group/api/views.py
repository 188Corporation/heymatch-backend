from typing import Any

from django.db.models.query import QuerySet
from rest_framework import status, viewsets
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

    ALLOWED_STEPS = (1, 2, 3, 4)

    queryset = Group.objects.all()
    permission_classes = [AllowAny]  # TODO

    def get_queryset(self) -> QuerySet:
        qs = self.queryset
        return qs

    def _check_step_num(self, step_num: int) -> bool:
        return step_num in self.ALLOWED_STEPS

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
        step_num = self.kwargs["step_num"]
        # check step validity
        if not self._check_step_num(step_num):
            return Response(
                data={"detail": f"Invalid step(={step_num}) parameter in the url."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pass

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        step_num = self.kwargs["step_num"]
        # check step validity
        if not self._check_step_num(step_num):
            return Response(
                data={"detail": f"Invalid step(={step_num}) parameter in the url."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        method = getattr(self, f"handle_step_{step_num}")
        method(
            request,
        )


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
