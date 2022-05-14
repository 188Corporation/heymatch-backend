from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.validators import (
    MaxValueValidator,
    MinValueValidator,
    RangeMaxValueValidator,
    RangeMinValueValidator,
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_google_maps.fields import GeoLocationField

from heythere.apps.user.models import User

from .managers import ActiveGroupInvitationCodeManager, ActiveGroupManager, GroupManager


def group_default_time():
    return timezone.now() + timezone.timedelta(hours=24)


class Group(models.Model):
    # Group GPS
    hotplace = models.ForeignKey(
        "search.HotPlace", blank=True, null=True, on_delete=models.PROTECT
    )
    gps_geoinfo = GeoLocationField(blank=True, null=True)
    gps_checked = models.BooleanField(blank=False, null=False, default=False)
    gps_last_check_time = models.DateTimeField(blank=True, null=True)

    # Group Profile
    title = models.CharField(
        _("Title of Group"), blank=False, null=False, max_length=100
    )
    introduction = models.TextField(blank=True, null=True, max_length=500)
    desired_other_group_member_number = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(2), MaxValueValidator(5)],
    )
    desired_other_group_member_avg_age_range = IntegerRangeField(
        blank=True,
        null=True,
        default=(20, 30),
        validators=[RangeMinValueValidator(20), RangeMaxValueValidator(50)],
    )

    # Registration Steps Status
    register_step_1_completed = models.BooleanField(
        blank=False, null=False, default=False
    )
    register_step_2_completed = models.BooleanField(
        blank=False, null=False, default=False
    )
    register_step_3_completed = models.BooleanField(
        blank=False, null=False, default=False
    )
    register_step_4_completed = models.BooleanField(
        blank=False, null=False, default=False
    )
    register_step_all_confirmed = models.BooleanField(
        blank=False, null=False, default=False
    )

    # Group Lifecycle
    is_active = models.BooleanField(blank=False, null=False, default=False)
    active_until = models.DateTimeField(
        blank=True, null=True, default=group_default_time
    )

    objects = GroupManager()
    active_objects = ActiveGroupManager()

    @property
    def member_number(self):
        user_manager = User.active_objects
        return user_manager.count_group_members(self)

    @property
    def member_avg_age(self):
        user_manager = User.active_objects
        return user_manager.count_group_members_avg_age(self)


def unique_random_code():
    while True:
        code = GroupInvitationCode.active_objects.generate_random_code(length=4)
        if not GroupInvitationCode.active_objects.filter(code=code).exists():
            return code


def invitation_code_default_time():
    return timezone.now() + timezone.timedelta(minutes=5)


class GroupInvitationCode(models.Model):
    user = models.ForeignKey(User, blank=False, null=False, on_delete=models.CASCADE)
    code = models.IntegerField(blank=False, null=False, default=unique_random_code)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    active_until = models.DateTimeField(
        blank=True, null=True, default=invitation_code_default_time
    )

    objects = models.Manager()
    active_objects = ActiveGroupInvitationCodeManager()
