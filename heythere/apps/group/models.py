from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.validators import (
    MaxValueValidator,
    MinValueValidator,
    RangeMaxValueValidator,
    RangeMinValueValidator,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_google_maps.fields import GeoLocationField

from .managers import ActiveGroupManager


class Group(models.Model):
    # Group GPS
    hotplace = models.ForeignKey(
        "search.HotPlace", blank=True, null=True, on_delete=models.PROTECT
    )
    gps_geo_location = GeoLocationField(blank=True, null=True)
    gps_checked = models.BooleanField(blank=False, null=False, default=False)
    gps_last_check_time = models.DateTimeField(blank=True, null=True)

    # Group Info
    member_number = models.IntegerField(blank=True, null=True)
    member_avg_age = models.IntegerField(blank=True, null=True)

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

    # Group Lifecycle
    is_active = models.BooleanField(blank=False, null=False, default=True)
    active_until = models.DateTimeField(blank=True, null=True)

    active_objects = ActiveGroupManager()


# class GroupPhoto(models.Model):
#     group = models.ForeignKey(Group, on_delete=models.CASCADE)
