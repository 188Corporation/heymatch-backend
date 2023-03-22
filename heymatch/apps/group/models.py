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

from .managers import ActiveGroupManager, GroupManager, GroupMemberManager


class EncryptedGeoLocationField(EncryptedField, GeoLocationField):
    """Encrypt user's geo-location in order to comply with Korea compliance (방통위 위치기반사업자)"""

    pass


class GroupV2(models.Model):
    class MeetUpTimeRange(models.TextChoices):
        LUNCH = "lunch"  # 11am ~ 2pm
        AFTERNOON = "afternoon"  # 2pm ~ 5pm
        DINNER = "dinner"  # 5pm ~ 8pm
        NIGHT = "night"  # 8pm ~
        NOT_SURE = "not_sure"

    title = models.CharField(blank=False, null=False, max_length=100)
    introduction = models.TextField(blank=False, null=False, max_length=500)
    meetup_date = models.DateField(blank=False, null=False)
    meetup_timerange = models.CharField(
        blank=False, null=False, choices=MeetUpTimeRange.choices, max_length=20
    )
    gps_geoinfo = EncryptedGeoLocationField(blank=False, null=False, max_length=20)

    # Lifecycle
    is_active = models.BooleanField(default=True)

    # History
    history = HistoricalRecords()

    @property
    def member_number(self):
        manager = GroupMember.objects
        return manager.count_group_members(self)

    @property
    def member_avg_height(self):
        manager = GroupMember.objects
        return manager.count_group_members_avg_height(self)

    @property
    def member_gender_type(self):
        manager = GroupMember.objects
        return manager.get_member_gender_type(self)


class GroupMember(models.Model):
    group = models.ForeignKey(
        "group.GroupV2",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="group_member_group",
    )
    user = models.ForeignKey(
        "user.User",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="group_member_user",
    )
    is_user_leader = models.BooleanField(default=False)

    # Lifecycle
    is_active = models.BooleanField(default=True)

    # History
    history = HistoricalRecords()

    objects = GroupMemberManager()


##################
# Deprecated - V1
##################


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
    title = models.CharField(blank=False, null=False, max_length=100)
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


# TODO(@jin): LEGACY - Should delete GroupProfileImage related models and endpoints
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
