from colorfield.fields import ColorField
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_google_maps import fields as map_fields

# from heytheymatchhere.apps.group.models import Group


class HotPlace(models.Model):
    name = models.CharField(
        _("Name of Hotplace"), blank=False, null=False, unique=True, max_length=32
    )
    zone_color = ColorField(default="#c7c7c7")  # #c7c7c7: grey
    zone_center_geoinfo = map_fields.GeoLocationField(blank=True, null=True)
    zone_boundary_geoinfos = ArrayField(
        map_fields.GeoLocationField(), blank=True, null=True
    )
