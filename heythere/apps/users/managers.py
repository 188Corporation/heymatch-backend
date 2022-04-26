from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import validate_email


class UserManager(BaseUserManager):
    def _create_user(
        self, username: str, phone_number: str, password, **extra_fields
    ):
        """
        Creates and saves a User with the given email and password.
        """
        user = self.model(
            username=username,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, username: str, phone_number: str, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(
            username, phone_number, password, **extra_fields
        )

    def create_superuser(self, username: str, phone_number: str, password, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self._create_user(
            username, phone_number, password, **extra_fields
        )
