from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.query import QuerySet
from phone_verify.models import SMSVerification
from phonenumber_field.phonenumber import to_python
from rest_auth.registration.serializers import RegisterSerializer
from rest_auth.serializers import LoginSerializer, UserDetailsSerializer
from rest_framework import exceptions, serializers

User = get_user_model()


class UserDetailByPhoneNumberSerializer(UserDetailsSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "phone_number",
            "birthdate",
            "gender",
            "height_cm",
            "workplace",
            "school",
        )
        read_only_fields = ("phone_number",)


class UserRegisterByPhoneNumberSerializer(RegisterSerializer):
    email = None
    username = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    phone_security_code = serializers.CharField(required=True)
    password1 = serializers.CharField(required=True, write_only=True)
    password2 = serializers.CharField(required=True, write_only=True)

    def get_cleaned_data(self):
        super(UserRegisterByPhoneNumberSerializer, self).get_cleaned_data()
        return {
            "username": self.validated_data.get("username", ""),
            "phone_number": self.validated_data.get("phone_number", ""),
            "phone_security_code": self.validated_data.get("phone_security_code", ""),
            "password1": self.validated_data.get("password1", ""),
            "password2": self.validated_data.get("password2", ""),
        }

    def save(self, request):
        phone_number = request.data["phone_number"]
        phone_security_code = request.data["phone_security_code"]
        username = request.data["username"]

        phone_number_python = to_python(phone_number)
        if not phone_number_python.is_valid():
            raise serializers.ValidationError(
                detail="Provided phone number is invalid. Please check country code or number"
            )

        if not self.check_if_phone_verified(phone_number, phone_security_code):
            raise serializers.ValidationError(detail="Invalid SMS verification info")

        if self.check_if_user_exists(username, phone_number):
            raise serializers.ValidationError(
                detail="User with same username or phone_number exists"
            )

        user = User.objects.create_user(
            username=username,
            phone_number=phone_number,
            password=request.data["password1"],
        )
        return user

    @staticmethod
    def check_if_phone_verified(phone_number: str, phone_security_code: str):
        qs: QuerySet = SMSVerification.objects.filter(
            phone_number=phone_number, security_code=phone_security_code
        )
        return qs.exists() and qs[0].is_verified

    @staticmethod
    def check_if_user_exists(username: str, phone_number: str):
        qs: QuerySet = User.objects.filter(
            Q(username=username) | Q(phone_number=phone_number)
        )
        return qs.exists()


class UserLoginByPhoneNumberSerializer(LoginSerializer):
    username = None
    email = None
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(style={"input_type": "password"})

    def _validate_phone_number(self, phone_number: str, password):
        if phone_number and password:
            # validate phone_number is verified
            qs: QuerySet = SMSVerification.objects.filter(phone_number=phone_number)
            if not qs.exists() or not qs[0].is_verified:
                msg = "Provided phone_number unverified."
                raise exceptions.ValidationError(detail=msg)

            # get user with phone_number
            qs: QuerySet = User.objects.filter(phone_number=phone_number)
            if not qs.exists():
                msg = "Provided phone_number never signed-up."
                raise exceptions.ValidationError(detail=str(msg))

            user = self._validate_username(qs[0].username, password)
        else:
            msg = 'Must include either "phone_number" and "password".'
            raise exceptions.ValidationError(detail=msg)
        return user

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")

        user = self._validate_phone_number(phone_number, password)

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


class GpsAuthenticationForGroupSerializer(serializers.ModelSerializer):
    pass
