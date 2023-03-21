import os.path
import random
import string
import uuid
from io import BytesIO
from uuid import uuid4

from birthday import BirthdayField
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from ordered_model.models import OrderedModel
from phonenumber_field.modelfields import PhoneNumberField
from PIL import Image, ImageFilter, ImageOps
from simple_history.models import HistoricalRecords

from .managers import (
    ActiveEmailVerificationCodeManager,
    ActiveUserManager,
    ActiveUserProfileManager,
    UserManager,
)

MAX_HEIGHT_CM = 210
MIN_HEIGHT_CM = 125
MAX_USERNAME_LENGTH = 10


def generate_random_username():
    return "".join(
        random.choice(string.ascii_letters) for _ in range(MAX_USERNAME_LENGTH)
    )


def free_pass_default_time():
    return timezone.now() + timezone.timedelta(hours=24)


class User(AbstractUser):
    class GenderChoices(models.TextChoices):
        MALE = "m"
        FEMALE = "f"

    class MaleBodyFormChoices(models.TextChoices):
        THIN = "thin"
        SLENDER = "slender"
        NORMAL = "normal"
        CHUBBY = "chubby"
        MUSCULAR = "muscular"
        BULKY = "bulky"

    class FemaleBodyFormChoices(models.TextChoices):
        THIN = "thin"
        SLENDER = "slender"
        NORMAL = "normal"
        CHUBBY = "chubby"
        GLAMOROUS = "glamorous"
        BULKY = "bulky"

    class JobChoices(models.TextChoices):
        COLLEGE_STUDENT = "college_student"
        EMPLOYEE = "employee"
        SELF_EMPLOYED = "self_employed"
        PART_TIME = "part_time"
        BUSINESSMAN = "businessman"
        ETC = "etc"

    # stream.io
    stream_token = models.TextField()

    # Basic Info
    id = models.UUIDField(
        primary_key=True, blank=False, null=False, editable=False, default=uuid4
    )
    # flag that points whether user is first signup or not
    # use this flag to decide to show registration form or not
    is_first_signup = models.BooleanField(default=True)
    username = models.CharField(
        unique=True,
        blank=False,
        null=False,
        editable=True,
        max_length=MAX_USERNAME_LENGTH,
        default=generate_random_username,
    )
    # Required
    phone_number = PhoneNumberField(blank=True, null=True)
    gender = models.CharField(
        blank=True, null=True, max_length=1, choices=GenderChoices.choices, default=None
    )
    birthdate = BirthdayField(blank=True, null=True, default=None)

    # Optional
    height_cm = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(MIN_HEIGHT_CM),
            MaxValueValidator(MAX_HEIGHT_CM),
        ],
    )
    male_body_form = models.CharField(
        blank=True, null=True, max_length=15, choices=MaleBodyFormChoices.choices
    )
    female_body_form = models.CharField(
        blank=True, null=True, max_length=15, choices=FemaleBodyFormChoices.choices
    )
    job_title = models.CharField(
        blank=True, null=True, max_length=32, choices=JobChoices.choices, default=None
    )
    verified_school_name = models.CharField(
        blank=True, null=True, max_length=32, default=None
    )
    verified_company_name = models.CharField(
        blank=True, null=True, max_length=32, default=None
    )

    # Group related
    # joined_group = models.ForeignKey(
    #     "group.Group",
    #     blank=True,
    #     null=True,
    #     on_delete=models.PROTECT,
    #     related_name="users",
    # )
    # is_group_leader = models.BooleanField(blank=False, null=False, default=False)

    # Purchase related
    point_balance = models.IntegerField(
        blank=False, null=False, default=settings.USER_INITIAL_POINT
    )
    free_pass = models.BooleanField(default=False)
    free_pass_active_until = models.DateTimeField(
        blank=True, null=True, default=free_pass_default_time
    )

    # Is real or fake?
    # this is needed for inviting non-heymatch user to group
    is_temp_user = models.BooleanField(default=False)

    # LifeCycle
    is_deleted = models.BooleanField(default=False)

    # History
    history = HistoricalRecords()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone_number"]

    objects = UserManager()
    active_objects = ActiveUserManager()


def upload_to(instance, filename):
    _, extension = filename.split(".")
    return f"{settings.AWS_S3_USER_PROFILE_PHOTO_FOLDER}/%s.%s" % (
        uuid.uuid4(),
        extension,
    )


class UserProfileImage(OrderedModel):
    class StatusChoices(models.TextChoices):
        NOT_VERIFIED = "n"
        UNDER_VERIFICATION = "u"
        ACCEPTED = "a"
        REJECTED = "r"

    user = models.ForeignKey(
        "user.User",
        null=False,
        on_delete=models.PROTECT,
        related_name="user_profile_images",
    )
    is_main = models.BooleanField(default=False)  # 메인 프로필 사진 (필수로 심사 받아야함)
    status = models.CharField(
        blank=True,
        null=True,
        default=StatusChoices.NOT_VERIFIED,
        choices=StatusChoices.choices,
        max_length=1,
    )
    image = models.ImageField(upload_to=upload_to)
    image_blurred = models.ImageField(upload_to=upload_to)
    thumbnail = models.ImageField(upload_to=upload_to)
    thumbnail_blurred = models.ImageField(upload_to=upload_to)

    # History
    history = HistoricalRecords()

    # ProfileImage Lifecycle
    is_active = models.BooleanField(blank=False, null=False, default=True)

    order_with_respect_to = "user"

    active_objects = ActiveUserProfileManager()

    def save(self, *args, **kwargs):
        image = Image.open(self.image)
        image = ImageOps.exif_transpose(image)  # fix ios image rotation bug

        # crop
        image_4x3 = self.crop_by_4x3(image)
        image_1x1 = self.crop_by_1x1(image)

        # process
        self.process_image(image_4x3)
        self.process_image_blurred(image_4x3)
        self.process_thumbnail(image_1x1)
        self.process_thumbnail_blurred(image_1x1)
        super(UserProfileImage, self).save(*args, **kwargs)

    def check_file_type(self):
        img_name, img_extension = os.path.splitext(self.image.name)
        img_extension = img_extension.lower()

        if img_extension in [".jpg", ".jpeg"]:
            return "JPEG"
        elif img_extension == ".gif":
            return "GIF"
        elif img_extension == ".png":
            return "PNG"
        else:
            return False  # Unrecognized file type

    @staticmethod
    def crop_by_4x3(image):
        """
        We always make sure that height is greater than width
        """
        width, height = image.size
        expected_height = width * (4 / 3)
        if height > expected_height:
            offset = int(abs((height - expected_height) / 2))
            image = image.crop([0, offset, width, height - offset])

        return image

    @staticmethod
    def crop_by_1x1(image):
        width, height = image.size
        if width == height:
            return image
        offset = int(abs(height - width) / 2)
        if width > height:
            image = image.crop(
                [offset, 0, width - offset, height]
            )  # left, upper, right, and lower
        else:
            image = image.crop([0, offset, width, height - offset])
        return image

    def process_image(self, image, filetype: str = "JPEG"):
        temp_image = BytesIO()
        image.save(temp_image, filetype)
        temp_image.seek(0)
        # set save=False, otherwise it will run in an infinite loop
        self.image.save(
            f"image_4x3.{filetype.lower()}",
            ContentFile(temp_image.read()),
            save=False,
        )
        temp_image.close()

    def process_image_blurred(self, image, filetype: str = "JPEG"):
        """
        Blurs image and save
        :return:
        """
        image = image.filter(ImageFilter.BoxBlur(10))
        temp_image = BytesIO()
        image.save(temp_image, filetype)
        temp_image.seek(0)
        # set save=False, otherwise it will run in an infinite loop
        self.image_blurred.save(
            f"image_4x3_blurred.{filetype.lower()}",
            ContentFile(temp_image.read()),
            save=False,
        )
        temp_image.close()

    def process_thumbnail(self, image, filetype: str = "JPEG"):
        """
        Creates thumbnail and blurred_thumbnail.
        """
        image.thumbnail((350, 350), Image.Resampling.LANCZOS)
        temp_image = BytesIO()
        image.save(temp_image, filetype)
        temp_image.seek(0)
        # set save=False, otherwise it will run in an infinite loop
        self.thumbnail.save(
            f"thumbnail_1x1.{filetype.lower()}",
            ContentFile(temp_image.read()),
            save=False,
        )
        temp_image.close()

    def process_thumbnail_blurred(self, image, filetype: str = "JPEG"):
        image.thumbnail((350, 350), Image.Resampling.LANCZOS)
        image = image.filter(ImageFilter.BoxBlur(5))
        # Save thumbnail to in-memory file as StringIO
        temp_image = BytesIO()
        image.save(temp_image, filetype)
        temp_image.seek(0)
        # set save=False, otherwise it will run in an infinite loop
        self.thumbnail_blurred.save(
            f"thumbnail_1x1_blurred.{filetype.lower()}",
            ContentFile(temp_image.read()),
            save=False,
        )
        temp_image.close()


def email_verification_code_valid_until():
    return timezone.now() + timezone.timedelta(minutes=3)


def auto_generate_email_verification_code():
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(5)
    )


class EmailVerificationCode(models.Model):
    class VerificationType(models.TextChoices):
        SCHOOL = "school"
        COMPANY = "company"

    email = models.EmailField(null=False, blank=False)
    type = models.CharField(
        null=False, blank=False, max_length=15, choices=VerificationType.choices
    )
    user = models.ForeignKey(
        "user.User",
        null=False,
        on_delete=models.PROTECT,
        related_name="user_email_verification_code",
    )
    code = models.CharField(max_length=5, default=auto_generate_email_verification_code)
    active_until = models.DateTimeField(default=email_verification_code_valid_until)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = ActiveEmailVerificationCodeManager()


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
