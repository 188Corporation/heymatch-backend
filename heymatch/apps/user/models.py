import random
import string
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

from .managers import ActiveUserManager, UserManager

# from django.core.validators import MaxValueValidator, MinValueValidator
# from birthday import BirthdayField


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
    phone_number = PhoneNumberField(null=False, blank=False)
    # age = models.IntegerField(blank=True, null=True)  # post create
    # birthdate = BirthdayField(blank=True, null=True)
    # gender = models.IntegerField(blank=True, null=True, choices=GENDER_CHOICES)
    # height_cm = models.IntegerField(
    #     blank=True,
    #     null=True,
    #     validators=[
    #         MinValueValidator(MIN_HEIGHT_CM),
    #         MaxValueValidator(MAX_HEIGHT_CM),
    #     ],
    # )
    #
    # workplace = models.CharField(blank=True, null=True, max_length=32)
    # school = models.CharField(blank=True, null=True, max_length=32)

    # Group related
    joined_group = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="users",
    )
    # is_group_leader = models.BooleanField(blank=False, null=False, default=False)

    # Purchase related
    point_balance = models.IntegerField(
        blank=False, null=False, default=settings.USER_INITIAL_POINT
    )
    free_pass = models.BooleanField(default=False)
    free_pass_active_until = models.DateTimeField(
        blank=True, null=True, default=free_pass_default_time
    )

    # LifeCycle
    is_deleted = models.BooleanField(default=False)

    # History
    history = HistoricalRecords()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone_number"]

    objects = UserManager()
    active_objects = ActiveUserManager()


def delete_schedule_default_time():
    return timezone.now() + timezone.timedelta(days=7)


class DeleteScheduledUser(models.Model):
    class DeleteStatusChoices(models.TextChoices):
        WAITING = "WAITING"
        COMPLETED = "COMPLETED"
        CANCELED = "CANCELED"

    user = models.ForeignKey(
        "user.User",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(default=timezone.now)
    delete_schedule_at = models.DateTimeField(default=delete_schedule_default_time)
    delete_reason = models.TextField(
        blank=True, null=True, max_length=500, default=None
    )
    status = models.CharField(
        max_length=24,
        choices=DeleteStatusChoices.choices,
        default=DeleteStatusChoices.WAITING,
    )


class FakeChatUser(models.Model):
    user = models.ForeignKey(
        "user.User",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name="fake_chat_user",
    )
    target_hotplace = models.ForeignKey(
        "hotplace.HotPlace",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name="fake_chat_user_hotplace",
    )


class AppInfo(models.Model):
    faq_url = models.URLField(max_length=200)  # 앱 문의, 건의
    terms_of_service_url = models.URLField(max_length=200)  # 이용약관
    privacy_policy_url = models.URLField(max_length=200)  # 개인정보처리방침
    terms_of_location_service_url = models.URLField(max_length=200)  # 위치기반서비스
    business_registration_url = models.URLField(max_length=200)  # 사업자정보
