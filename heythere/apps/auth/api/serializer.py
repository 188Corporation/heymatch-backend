from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from phone_verify.models import SMSVerification
from rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from django.db.models import Q

User = get_user_model()


class UserRegisterByPhoneSerializer(RegisterSerializer):
    email = None
    username = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    phone_security_code = serializers.CharField(required=True)
    password1 = serializers.CharField(required=True, write_only=True)
    password2 = serializers.CharField(required=True, write_only=True)

    def get_cleaned_data(self):
        super(UserRegisterByPhoneSerializer, self).get_cleaned_data()
        return {
            'username': self.validated_data.get('username', ''),
            'phone_number': self.validated_data.get('phone_number', ''),
            'phone_security_code': self.validated_data.get('phone_security_code', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
        }

    def save(self, request):
        phone_number = request.data["phone_number"]
        phone_security_code = request.data["phone_security_code"]
        username = request.data["username"]

        if not self.check_if_phone_verified(phone_number, phone_security_code):
            raise serializers.ValidationError("Invalid SMS verification info")

        if self.check_if_user_exists(username, phone_number):
            raise serializers.ValidationError("User with same username or phone_number exists")

        user = User.objects.create_user(
            username=username,
            phone_number=phone_number,
            password=request.data["password1"],
        )
        return user

    @staticmethod
    def check_if_phone_verified(phone_number: str, phone_security_code: str):
        qs: QuerySet = SMSVerification.objects.filter(phone_number=phone_number,
                                                      security_code=phone_security_code)
        return qs.exists() and qs[0].is_verified

    @staticmethod
    def check_if_user_exists(username: str, phone_number: str):
        qs: QuerySet = User.objects.filter(Q(username=username) | Q(phone_number=phone_number))
        return qs.exists()
