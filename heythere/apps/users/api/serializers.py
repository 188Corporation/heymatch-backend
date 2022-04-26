from django.contrib.auth import get_user_model
from phone_verify.serializers import SMSVerificationSerializer
from rest_framework import serializers

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]


class UserSMSVerificationSerializer(UserDetailSerializer, SMSVerificationSerializer):
    pass
