from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_google_maps import fields as map_fields

from .managers import ActiveHotplaceManager


class HotPlace(models.Model):
    name = models.CharField(
        _("Name of Hotplace"), blank=False, null=False, unique=True, max_length=32
    )
    # zone_color = ColorField(default="#c7c7c7")  # #c7c7c7: grey
    zone_center_geoinfo = map_fields.GeoLocationField(blank=True, null=True)
    zone_boundary_geoinfos = ArrayField(
        map_fields.GeoLocationField(), blank=True, null=True
    )
    zone_boundary_geoinfos_for_fake_chat = ArrayField(
        map_fields.GeoLocationField(), blank=True, null=True
    )
    is_active = models.BooleanField(default=True)

    objects = models.Manager
    active_objects = ActiveHotplaceManager

    def __str__(self):
        return self.name
