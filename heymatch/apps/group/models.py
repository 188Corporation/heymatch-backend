import os.path
import uuid
from io import BytesIO

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.operations import CreateExtension
from django.core.files.base import ContentFile
from django.db import migrations
from django.utils import timezone
from django.utils.timezone import now
from django_google_maps.fields import GeoLocationField
from fernet_fields import EncryptedField
from ordered_model.models import OrderedModel
from PIL import Image, ImageFilter, ImageOps
from simple_history.models import HistoricalRecords

from .managers import ActiveGroupManager, GroupManager, GroupMemberManager


class EncryptedGeoLocationField(EncryptedField, GeoLocationField):
    """Encrypt user's geo-location in order to comply with Korea compliance (방통위 위치기반사업자)"""

    pass


class Migration(migrations.Migration):
    operations = [
        CreateExtension("postgis"),
    ]


class GroupV2(models.Model):
    class GroupMode(models.TextChoices):
        SIMPLE = "simple"
        INVITE = "invite"

    class MeetUpTimeRange(models.TextChoices):
        LUNCH = "lunch"  # 11am ~ 2pm
        AFTERNOON = "afternoon"  # 2pm ~ 5pm
        DINNER = "dinner"  # 5pm ~ 8pm
        NIGHT = "night"  # 8pm ~
        NOT_SURE = "not_sure"

    class GroupWhoWeAreTag(models.TextChoices):
        A_LOT_OF_CUTENESS = ("A_LOT_OF_CUTENESS", "😘 애교가 많아요/rgba(217,225,239,1.0)")
        A_LOT_OF_PLAYFULNESS = (
            "A_LOT_OF_PLAYFULNESS",
            "😝 장난기가 많아요/rgba(217,225,239,1.0)",
        )
        INTERNATIONAL = ("INTERNATIONAL", "🌏 다국적이에요/rgba(217,225,239,1.0)")
        A_LOT_OF_ACTIVENESS = ("A_LOT_OF_ACTIVENESS", "😃 활달해요/rgba(217,225,239,1.0)")
        TENDS_TO_BE_QUIET = ("TENDS_TO_BE_QUIET", "😷 조용한 편이에요/rgba(217,225,239,1.0)")
        A_LOT_OF_SHYNESS = ("A_LOT_OF_SHYNESS", "🙈 수줍음이 많아요/rgba(217,225,239,1.0)")
        NICE_BODY_SHAPE = ("NICE_BODY_SHAPE", "👍 몸매가 좋아요/rgba(217,225,239,1.0)")
        WE_ARE_HANDSOME = ("WE_ARE_HANDSOME", "🤩 잘생겼어요/rgba(217,225,239,1.0)")
        WE_ARE_PRETTY = ("WE_ARE_PRETTY", "😍 예뻐요/rgba(217,225,239,1.0)")
        WE_ARE_GOOD_LOOKING = ("WE_ARE_GOOD_LOOKING", "☺️ 훈훈해요/rgba(217,225,239,1.0)")
        FASHION_PEOPLE = ("FASHION_PEOPLE", "🕶 패셔니스타/rgba(217,225,239,1.0)")
        WE_ARE_KING = ("WE_ARE_KING", "👑 이 구역의 왕은 우리야/rgba(217,225,239,1.0)")
        WE_LIKE_SPORTS = ("WE_LIKE_SPORTS", "💪 운동을 좋아해요/rgba(217,225,239,1.0)")
        A_LOT_OF_LAUGHING = ("A_LOT_OF_LAUGHING", "🤣 웃음이 많아요/rgba(217,225,239,1.0)")
        GOOD_AT_TALKING = ("GOOD_AT_TALKING", "💬 대화를 잘해요/rgba(217,225,239,1.0)")
        WE_ARE_HUMOROUS = ("WE_ARE_HUMOROUS", "😂 유머러스해요/rgba(217,225,239,1.0)")

    class GroupWantToMeetTag(models.TextChoices):
        WE_LIKE_WINE = ("WE_LIKE_WINE", "🍷 와인 좋아해요/rgba(217,225,239,1.0)")
        WE_LIKE_BEER = ("WE_LIKE_BEER", "🍺 맥주 좋아해요/rgba(217,225,239,1.0)")
        WE_LIKE_MEAT = ("WE_LIKE_MEAT", "🍖 고기 먹어요/rgba(217,225,239,1.0)")
        WE_LIKE_SOJU = ("WE_LIKE_SOJU", "💚 소주 좋아해요/rgba(217,225,239,1.0)")
        WE_LIKE_SOUP = ("WE_LIKE_SOUP", "🍲 국물 안주 먹어요/rgba(217,225,239,1.0)")
        LETS_PLAY_ALCOHOL_GAME = (
            "LETS_PLAY_ALCOHOL_GAME",
            "🎮 술게임해요/rgba(217,225,239,1.0)",
        )
        LETS_TALK = ("LETS_TALK", "💬 차분히 대화해요/rgba(217,225,239,1.0)")
        WE_EAT_ANYTHING = ("WE_EAT_ANYTHING", "🤔 아무거나 먹어요/rgba(217,225,239,1.0)")
        WE_EAT_CHICKEN = ("WE_EAT_CHICKEN", "🍗 치킨 먹어요/rgba(217,225,239,1.0)")
        LETS_PLAY_HOT = ("LETS_PLAY_HOT", "🔥 화끈하게 놀아요/rgba(217,225,239,1.0)")
        PLAY_UNTIL_END = ("PLAY_UNTIL_END", "💪 끝까지 달려요/rgba(217,225,239,1.0)")
        PLAY_SIMPLE_UNTIL_FIRST = (
            "PLAY_SIMPLE_UNTIL_FIRST",
            "🍻 1차로만 가볍게 놀아요/rgba(217,225,239,1.0)",
        )
        DRINK_MAKGULI = ("DRINK_MAKGULI", "☂️ 비 오는 날은 막걸리/rgba(217,225,239,1.0)")

    mode = models.CharField(
        blank=False, null=False, choices=GroupMode.choices, max_length=10
    )
    title = models.CharField(blank=False, null=False, max_length=100)
    introduction = models.TextField(blank=False, null=False, max_length=500)
    meetup_date = models.DateField(blank=False, null=False)
    meetup_timerange = models.CharField(
        blank=True, null=True, choices=MeetUpTimeRange.choices, max_length=20
    )
    meetup_place_title = models.CharField(
        blank=False, null=False, max_length=250
    )  # from client
    meetup_place_address = models.CharField(
        blank=False, null=False, max_length=250
    )  # from client
    gps_point = models.PointField(geography=True, blank=False, null=False)
    gps_address = models.CharField(
        blank=False, null=False, max_length=250
    )  # NAVER reverse geocoded address. For Top rank aggregation purpose
    member_number = models.IntegerField(blank=True, null=True)
    member_avg_age = models.IntegerField(blank=True, null=True)

    # Match
    photo_point = models.IntegerField(
        blank=False, null=False, default=settings.POINT_NEEDED_FOR_PHOTO
    )  # Point for requesting match to this group
    match_point = models.IntegerField(
        blank=False, null=False, default=settings.POINT_NEEDED_FOR_MATCH
    )  # Point for requesting match to this group

    # Tags
    about_our_group_tags = ArrayField(
        models.TextField(
            blank=True, null=True, choices=GroupWhoWeAreTag.choices, max_length=128
        ),
        blank=True,
        null=True,
    )
    meeting_we_want_tags = ArrayField(
        models.TextField(
            blank=True, null=True, choices=GroupWantToMeetTag.choices, max_length=128
        ),
        blank=True,
        null=True,
    )

    # Lifecycle
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(default=now, editable=True)
    is_active = models.BooleanField(default=True)

    # History
    history = HistoricalRecords()

    # @property
    # def member_number(self):
    #     if not self.member_number:
    #         manager = GroupMember.objects
    #         return manager.count_group_members(self)
    #     return self.member_number

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


class Recent24HrTopGroupAddress(models.Model):
    result = models.JSONField(
        null=False, blank=False, default=dict
    )  # should use RawJSON to keep dict order intact
    aggregated_at = models.DateTimeField(default=now, editable=False)


class ReportedGroupV2(models.Model):
    class ReportGroupStatusChoices(models.TextChoices):
        REPORTED = "REPORTED"
        UNDER_REVIEW = "UNDER_REVIEW"
        PROCESSED = "PROCESSED"

    reported_group = models.ForeignKey(
        "group.GroupV2",
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


class GroupProfilePhotoPurchased(models.Model):
    class PurchaseMethodChoices(models.IntegerChoices):
        POINT = 0
        ADVERTISEMENT = 1

    buyer = models.ForeignKey(
        "user.User",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name="purchased_group_buyer",
    )
    seller = models.ForeignKey(
        "group.GroupV2",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name="purchased_group_seller",
    )
    method = models.IntegerField(
        blank=False,
        null=False,
        default=PurchaseMethodChoices.POINT,
        choices=PurchaseMethodChoices.choices,
    )

    # History
    created_at = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()


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
