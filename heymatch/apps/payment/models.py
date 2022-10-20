from colorfield.fields import ColorField
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_google_maps import fields as map_fields

# from heytheymatchhere.apps.group.models import Group


class PurchaseItem(models.Model):
    name = models.CharField(
        _("Name of Purchase Item"), blank=False, null=False, unique=True, max_length=32
    )
    price_in_krw = models.IntegerField()
