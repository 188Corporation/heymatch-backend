from birthday import BirthdayField
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.validators import (
    RangeMaxValueValidator,
    RangeMinValueValidator,
)
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from .managers import ActiveUserManager

GENDER_CHOICES = (
    (0, "male"),
    (1, "female"),
    (2, "not specified"),
)

MAX_HEIGHT_CM = 250
MIN_HEIGHT_CM = 100


class User(AbstractUser):
    # Basic Info
    phone_number = PhoneNumberField(null=False, blank=False, unique=True)
    age = models.IntegerField(blank=True, null=True)  # post create
    birthdate = BirthdayField(blank=True, null=True)
    gender = models.IntegerField(blank=True, null=True, choices=GENDER_CHOICES)
    height_cm = IntegerRangeField(
        blank=True,
        null=True,
        validators=[
            RangeMinValueValidator(MIN_HEIGHT_CM),
            RangeMaxValueValidator(MAX_HEIGHT_CM),
        ],
    )

    workplace = models.CharField(blank=True, null=True, max_length=32)
    school = models.CharField(blank=True, null=True, max_length=32)

    # Group related
    joined_group = models.ForeignKey(
        "group.Group", blank=True, null=True, on_delete=models.SET_NULL
    )
    is_group_leader = models.BooleanField(blank=False, null=False, default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone_number"]

    active_objects = ActiveUserManager()
