from datetime import date

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from heythere.apps.group.models import Group

from .managers import UserManager


def validate_birth_year(value: int):
    if value not in range(1900, date.today().year):
        raise ValidationError(
            _("%(value)s is not a valid birth year"),
            params={"value": value},
        )


def validate_height_cm(value: int):
    if value not in range(100, 300):
        raise ValidationError(
            _("%(value)s is not a valid height in centi-meter"),
            params={"value": value},
        )


GENDER_CHOICES = (
    (0, "male"),
    (1, "female"),
    (2, "not specified"),
)


class User(AbstractUser):
    # Basic Info
    phone_number = PhoneNumberField(null=False, blank=False, unique=True)
    birth_year = models.IntegerField(
        blank=True, null=True, validators=[validate_birth_year]
    )
    gender = models.IntegerField(blank=True, null=True, choices=GENDER_CHOICES)
    height_cm = models.IntegerField(
        blank=True, null=True, validators=[validate_height_cm]
    )
    workplace = models.CharField(blank=True, null=True, max_length=32)
    school = models.CharField(blank=True, null=True, max_length=32)

    # Group related
    joined_group = models.ForeignKey(
        Group, blank=True, null=True, on_delete=models.SET_NULL
    )
    is_group_leader = models.BooleanField(blank=False, null=False, default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone_number"]

    objects = UserManager()
