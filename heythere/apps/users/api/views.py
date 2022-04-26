from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from phone_verify.api import VerificationViewSet
from phone_verify.serializers import SMSVerificationSerializer
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import UserDetailSerializer, UserSMSVerificationSerializer

User = get_user_model()


class UserDetailViewSet(RetrieveAPIView):
    serializer_class = UserDetailSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, id=self.request.user.id)
        return obj


class UserSMSVerificationViewSet(VerificationViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserSMSVerificationSerializer

    @action(detail=False, methods=['POST'])
    def verify_and_register(self, request):
        # Verify SMS
        serializer = SMSVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create User
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.create_user_with_sms(**serializer.validated_data)

        return Response(serializer.data)

    @staticmethod
    def create_user_with_sms(username, phone_number, password, **extra_args):
        user = User.objects.create_user(
            username=username, phone_number=phone_number, password=password, **extra_args
        )
        return user
