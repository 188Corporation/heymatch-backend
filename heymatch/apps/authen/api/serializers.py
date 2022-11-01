from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, UserDetailsSerializer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from phone_verify.models import SMSVerification
from phone_verify.serializers import SMSVerificationSerializer
from phonenumber_field.phonenumber import to_python
from rest_framework import exceptions, serializers

User = get_user_model()
stream = settings.STREAM_CLIENT


class UserDetailByPhoneNumberSerializer(UserDetailsSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "stream_token",
            "username",
            "phone_number",
            "birthdate",
            "gender",
            "height_cm",
            "workplace",
            "school",
        )
        read_only_fields = ("phone_number",)


class UserLoginByPhoneNumberSerializer(LoginSerializer):
    username = None
    email = None
    password = None
    phone_number = serializers.CharField(required=True)
    session_token = serializers.CharField(required=True)
    security_code = serializers.CharField(required=True)

    def _validate_user(self, phone_number: str):
        if phone_number:
            # validate phone_number is verified
            qs: QuerySet = SMSVerification.objects.filter(phone_number=phone_number)
            if not qs.exists() or not qs[0].is_verified:
                msg = "Provided phone_number unverified."
                raise exceptions.ValidationError(detail=msg)

            # get user with phone_number
            user, created = User.objects.get_or_create(phone_number=phone_number)
            if created:
                # Register Stream token
                user.stream_token = stream.create_token(user_id=str(user.id))
                user.save()
                stream.upsert_user({"id": str(user.id), "role": "user"})
        else:
            msg = 'Must include "phone_number".'
            raise exceptions.ValidationError(detail=msg)
        return user

    def validate(self, attrs):
        # first verify SMS
        serializer = SMSVerificationSerializer(data=attrs)
        serializer.is_valid(raise_exception=True)

        # process login or registration
        phone_number = attrs.get("phone_number")
        user = self._validate_user(phone_number)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = "User account is disabled."
                raise exceptions.ValidationError(detail=msg)
        else:
            msg = "Unable to log in with provided credentials."
            raise exceptions.ValidationError(detail=str(msg))

        attrs["user"] = user
        return attrs


# DEPRECATED
class UserRegisterByPhoneNumberSerializer(RegisterSerializer):
    email = None
    phone_number = serializers.CharField(required=True)
    phone_security_code = serializers.CharField(required=True)
    password1 = serializers.CharField(required=True, write_only=True)
    password2 = serializers.CharField(required=True, write_only=True)

    def get_cleaned_data(self):
        super(UserRegisterByPhoneNumberSerializer, self).get_cleaned_data()
        return {
            "phone_number": self.validated_data.get("phone_number", ""),
            "phone_security_code": self.validated_data.get("phone_security_code", ""),
            "password1": self.validated_data.get("password1", ""),
            "password2": self.validated_data.get("password2", ""),
        }

    def save(self, request):
        phone_number = request.data["phone_number"]
        phone_security_code = request.data["phone_security_code"]

        phone_number_python = to_python(phone_number)
        if not phone_number_python.is_valid():
            raise serializers.ValidationError(
                detail="Provided phone number is invalid. Please check country code or number"
            )

        if not self.check_if_phone_verified(phone_number, phone_security_code):
            raise serializers.ValidationError(detail="Invalid SMS verification info")

        if self.check_if_user_exists(phone_number):
            raise serializers.ValidationError(
                detail="User with same username or phone_number exists"
            )

        user = User.objects.create_user(
            phone_number=phone_number,
            password=request.data["password1"],
        )

        # Register Stream token
        stream.upsert_user({"id": str(user.id), "role": "user"})

        return user

    @staticmethod
    def check_if_phone_verified(phone_number: str, phone_security_code: str):
        qs: QuerySet = SMSVerification.objects.filter(
            phone_number=phone_number, security_code=phone_security_code
        )
        return qs.exists() and qs[0].is_verified

    @staticmethod
    def check_if_user_exists(phone_number: str):
        qs: QuerySet = User.objects.filter(phone_number=phone_number)
        return qs.exists()
