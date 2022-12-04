import os.path
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django_google_maps.fields import GeoLocationField
from fernet_fields import EncryptedField
from ordered_model.models import OrderedModel
from PIL import Image, ImageFilter, ImageOps
from simple_history.models import HistoricalRecords

from .managers import ActiveGroupManager, GroupManager


class EncryptedGeoLocationField(EncryptedField, GeoLocationField):
    """Encrypt user's geo-location in order to comply with Korea compliance (방통위 위치기반사업자)"""

    pass


class Group(models.Model):
    # Group GPS
    hotplace = models.ForeignKey(
        "hotplace.HotPlace",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="groups",
    )
    gps_geoinfo = EncryptedGeoLocationField(blank=False, null=False, max_length=20)
    # gps_checked = models.BooleanField(blank=False, null=False, default=False)
    # gps_last_check_time = models.DateTimeField(blank=True, null=True)

    # Group Profile
    title = models.CharField("Title of Group", blank=False, null=False, max_length=100)
    introduction = models.TextField(blank=False, null=False, max_length=500)
    male_member_number = models.IntegerField(
        blank=True,
        null=True,
    )
    female_member_number = models.IntegerField(
        blank=True,
        null=True,
    )
    member_average_age = models.IntegerField(
        blank=True,
        null=True,
    )
    match_point = models.IntegerField(
        blank=False, null=False, default=1
    )  # Point for requesting match to this group

    #########
    # LEGACY
    #########
    # desired_other_group_member_number = models.IntegerField(
    #     blank=True,
    #     null=True,
    #     validators=[MinValueValidator(2), MaxValueValidator(5)],
    # )
    # desired_other_group_member_avg_age_range = IntegerRangeField(
    #     blank=True,
    #     null=True,
    #     validators=[RangeMinValueValidator(20), RangeMaxValueValidator(50)],
    # )

    # Group Lifecycle
    is_active = models.BooleanField(blank=False, null=False, default=True)
    is_deleted = models.BooleanField(blank=False, null=False, default=False)
    # active_until = models.DateTimeField(
    #     blank=True, null=True, default=group_default_time
    # )

    # History
    history = HistoricalRecords()

    objects = GroupManager()
    active_objects = ActiveGroupManager()

    # @property
    # def member_number(self):
    #     user_manager = User.active_objects
    #     return user_manager.count_group_members(self)

    # @property
    # def member_avg_age(self):
    #     user_manager = User.active_objects
    #     return user_manager.count_group_members_avg_age(self)


def upload_to(instance, filename):
    _, extension = filename.split(".")
    return f"{settings.AWS_S3_GROUP_PHOTO_FOLDER}/%s.%s" % (uuid.uuid4(), extension)


class GroupProfileImage(OrderedModel):
    group = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="group_profile_images",
    )
    image = models.ImageField(upload_to=upload_to)
    image_blurred = models.ImageField(upload_to=upload_to)
    thumbnail = models.ImageField(upload_to=upload_to)
    thumbnail_blurred = models.ImageField(upload_to=upload_to)

    # History
    history = HistoricalRecords()

    order_with_respect_to = "group"

    def save(self, *args, **kwargs):
        # ftype = self.check_file_type()
        # if not ftype:
        #     raise Exception("Could not process image - is the file type valid?")

        image = Image.open(self.image)
        image = ImageOps.exif_transpose(image)  # fix ios image rotation bug

        self.process_image_blurred(image)
        self.process_thumbnail(image)
        self.process_thumbnail_blurred(image)
        super(GroupProfileImage, self).save(*args, **kwargs)

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
            f"image_blurred.{filetype.lower()}",
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
            f"thumbnail.{filetype.lower()}", ContentFile(temp_image.read()), save=False
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
            f"thumbnail_blurred.{filetype.lower()}",
            ContentFile(temp_image.read()),
            save=False,
        )
        temp_image.close()


class ReportedGroup(models.Model):
    class ReportGroupStatusChoices(models.TextChoices):
        REPORTED = "REPORTED"
        UNDER_REVIEW = "UNDER_REVIEW"
        PROCESSED = "PROCESSED"

    reported_group = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    reported_reason = models.TextField(max_length=500, null=True, blank=True)
    reported_by = models.ForeignKey(
        "user.User",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="reported_by_user",
    )
    status = models.CharField(
        max_length=32,
        default=ReportGroupStatusChoices.REPORTED,
        choices=ReportGroupStatusChoices.choices,
    )
    created_at = models.DateTimeField(default=timezone.now)


# ========================
#  DEPRECATED
# ========================

# def blacklist_default_time():
#     return timezone.now() + timezone.timedelta(hours=24)

# class GroupBlackList(models.Model):
#     group = models.ForeignKey(
#         Group,
#         blank=False,
#         null=False,
#         on_delete=models.CASCADE,
#         related_name="blacklist_group",
#     )
#     blocked_group = models.ForeignKey(
#         Group,
#         blank=False,
#         null=False,
#         on_delete=models.CASCADE,
#         related_name="blacklist_blocked_group",
#     )
#
#     # Lifecycle
#     is_active = models.BooleanField(blank=False, null=False, default=True)
#     active_until = models.DateTimeField(
#         blank=True, null=True, default=blacklist_default_time
#     )
#
#     objects = GroupBlackListManager()
#     active_objects = ActiveGroupBlackListManager()

# def unique_random_code():
#     while True:
#         code = GroupInvitationCode.active_objects.generate_random_code(length=4)
#         if not GroupInvitationCode.active_objects.filter(code=code).exists():
#             return code
#
#
# def invitation_code_default_time():
#     return timezone.now() + timezone.timedelta(minutes=5)


# class GroupInvitationCode(models.Model):
#     user = models.ForeignKey(User, blank=False, null=False, on_delete=models.CASCADE)
#     code = models.IntegerField(blank=False, null=False, default=unique_random_code)
#     is_active = models.BooleanField(blank=False, null=False, default=True)
#     active_until = models.DateTimeField(
#         blank=True, null=True, default=invitation_code_default_time
#     )
#
#     objects = models.Manager()
#     active_objects = ActiveGroupInvitationCodeManager()
