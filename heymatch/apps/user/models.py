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

from .managers import ActiveUserManager, ActiveUserProfileManager, UserManager

MAX_HEIGHT_CM = 210
MIN_HEIGHT_CM = 155
MAX_USERNAME_LENGTH = 10


def generate_random_username():
    return "".join(
        random.choice(string.ascii_letters) for _ in range(MAX_USERNAME_LENGTH)
    )


def free_pass_default_time():
    return timezone.now() + timezone.timedelta(hours=24)


class User(AbstractUser):
    GENDER_CHOICES = (
        ("m", "Male"),
        ("f", "Female"),
        ("o", "Other"),
    )
    BODY_FORM_CHOICES = (
        ("thin", "마른"),
        ("slender", "슬림탄탄"),
        ("normal", "보통"),
        ("chubby", "통통한"),
        ("muscular", "근육질의"),
        ("bulky", "덩치가있는"),
    )
    FINAL_EDUCATION_CHOICES = (
        ("high_school", "고등학교"),
        ("bachelor", "학사"),
        ("master_or_above", "석박사"),
        ("medical_graduate", "의/약/치전원"),
        ("law_school", "로스쿨"),
        ("etc", "기타"),
    )
    JOB_CHOICES = (
        ("college_student", "대학생"),
        ("employee", "직장인"),
        ("self_employed", "자영업"),
        ("part_time", "파트타임"),
        ("businessman", "사업가"),
        ("etc", "기타"),
    )
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
        blank=True, null=True, max_length=1, choices=GENDER_CHOICES, default=None
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
    body_form = models.CharField(
        blank=True, null=True, max_length=15, choices=BODY_FORM_CHOICES
    )
    # 학력 관련
    final_education = models.CharField(
        blank=True,
        null=True,
        max_length=32,
        choices=FINAL_EDUCATION_CHOICES,
        default=None,
    )  # 최종 학력

    school_name = models.CharField(
        blank=True, null=True, max_length=32, default=None
    )  # 학교 이름
    is_school_verified = models.BooleanField(default=False)  # 학교 인증 여부
    # 직업 관련
    job_title = models.CharField(
        blank=True, null=True, max_length=32, choices=JOB_CHOICES, default=None
    )
    is_company_verified = models.BooleanField(default=False)  # 직업=직장인 경우에만

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

    # Agreement
    agreed_to_terms = models.BooleanField(default=False)

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
    user = models.ForeignKey(
        "user.User",
        null=False,
        on_delete=models.PROTECT,
        related_name="user_profile_images",
    )
    is_main = models.BooleanField(default=False)  # 메인 프로필 사진 (필수로 심사받아야함)
    is_verified = models.BooleanField(default=False)  # 심사완료
    image = models.ImageField(upload_to=upload_to)
    image_blurred = models.ImageField(upload_to=upload_to)
    thumbnail = models.ImageField(upload_to=upload_to)
    thumbnail_blurred = models.ImageField(upload_to=upload_to)

    # History
    history = HistoricalRecords()

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
