import random
import string
from uuid import uuid4

from birthday import BirthdayField
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from .managers import ActiveUserManager, UserManager

GENDER_CHOICES = (
    (0, "male"),
    (1, "female"),
    (2, "not specified"),
)

FREE_PASS_CHOICES = ((0, "one-day-pass"),)

MAX_HEIGHT_CM = 195
MIN_HEIGHT_CM = 155
MAX_USERNAME_LENGTH = 10


def generate_random_username():
    return "".join(
        random.choice(string.ascii_letters) for _ in range(MAX_USERNAME_LENGTH)
    )


def free_pass_default_time():
    return timezone.now() + timezone.timedelta(hours=24)


class User(AbstractUser):
    # stream.io
    stream_token = models.TextField()

    # Basic Info
    id = models.UUIDField(
        primary_key=True, blank=False, null=False, editable=False, default=uuid4
    )
    username = models.CharField(
        unique=True,
        blank=False,
        null=False,
        editable=True,
        max_length=MAX_USERNAME_LENGTH,
        default=generate_random_username,
    )
    phone_number = PhoneNumberField(null=False, blank=False, unique=True)
    age = models.IntegerField(blank=True, null=True)  # post create
    birthdate = BirthdayField(blank=True, null=True)
    gender = models.IntegerField(blank=True, null=True, choices=GENDER_CHOICES)
    height_cm = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(MIN_HEIGHT_CM),
            MaxValueValidator(MAX_HEIGHT_CM),
        ],
    )

    workplace = models.CharField(blank=True, null=True, max_length=32)
    school = models.CharField(blank=True, null=True, max_length=32)

    # Group related
    joined_group = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    is_group_leader = models.BooleanField(blank=False, null=False, default=False)

    # Purchase related
    point_balance = models.IntegerField(blank=False, null=False, default=0)
    free_pass = models.BooleanField(default=False)
    free_pass_active_until = models.DateTimeField(
        blank=True, null=True, default=free_pass_default_time
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone_number"]

    objects = UserManager()
    active_objects = ActiveUserManager()
