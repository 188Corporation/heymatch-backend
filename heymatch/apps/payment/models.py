from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models

from .managers import PlayStoreValidatedReceiptManager

User = get_user_model()


class PointItem(models.Model):
    name = models.CharField(blank=False, null=False, unique=True, max_length=32)
    product_id = models.CharField(blank=False, null=False, unique=True, max_length=128)
    price_in_krw = models.IntegerField(blank=False, null=False)
    default_point = models.IntegerField(blank=False, null=False)
    bonus_point = models.IntegerField(blank=True, null=True, default=0)
    best_deal_check = models.BooleanField(blank=True, null=True, default=False)

    @property
    def krw_per_point(self):
        return round(self.price_in_krw / (self.default_point + self.bonus_point), 2)


class FreePassItem(models.Model):
    name = models.CharField(blank=False, null=False, unique=True, max_length=32)
    product_id = models.CharField(blank=False, null=False, unique=True, max_length=128)
    price_in_krw = models.IntegerField(blank=False, null=False)
    free_pass_duration_in_hour = models.IntegerField(blank=False, null=False)
    best_deal_check = models.BooleanField(blank=True, null=True, default=False)


class PlayStoreValidatedReceipt(models.Model):
    # Receipt info
    orderId = models.CharField(max_length=48)
    packageName = models.CharField(max_length=48)
    productId = models.CharField(max_length=48)
    quantity = models.IntegerField()
    purchaseToken = models.TextField(max_length=250)

    # Verification result
    purchaseTimeMillis = models.IntegerField()
    purchaseState = models.IntegerField()
    consumptionState = models.IntegerField()
    developerPayload = models.CharField(max_length=120)
    # if prod, this field does not exist
    purchaseType = models.IntegerField(null=True, blank=True, default=None)
    acknowledgementState = models.IntegerField()
    kind = models.CharField(max_length=48)
    regionCode = models.CharField(max_length=8)

    objects = PlayStoreValidatedReceiptManager()


class AppleStoreValidatedReceipt(models.Model):
    pass


PLATFORM_CHOICES = (
    ("android", "android"),
    ("ios", "ios"),
)


class UserPurchase(models.Model):
    """
    Stores validated receipt, and point or subscription purchased item info.
    """

    id = models.UUIDField(
        primary_key=True, blank=False, null=False, editable=False, default=uuid4
    )
    UserPurchase = models.ForeignKey(
        User, blank=False, null=False, on_delete=models.CASCADE
    )
    platform = models.CharField(
        null=False, blank=False, choices=PLATFORM_CHOICES, max_length=8
    )
    play_store_receipt = models.OneToOneField(
        PlayStoreValidatedReceipt,
        null=True,
        blank=True,
        default=None,
        on_delete=models.PROTECT,
    )
    apple_store_receipt = models.OneToOneField(
        AppleStoreValidatedReceipt,
        null=True,
        blank=True,
        default=None,
        on_delete=models.PROTECT,
    )
    purchase_processed = models.BooleanField(default=False)  # add up jelly etc
