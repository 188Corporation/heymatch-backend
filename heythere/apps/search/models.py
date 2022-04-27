from colorfield.fields import ColorField
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_google_maps import fields as map_fields


class HotPlace(models.Model):
    name = models.CharField(
        _("Name of Hotplace"), blank=False, null=False, unique=True, max_length=32
    )
    zone_color = ColorField(default="#c7c7c7")  # #c7c7c7: grey
    zone_boundary_info = ArrayField(
        map_fields.GeoLocationField(), blank=False, null=False
    )
