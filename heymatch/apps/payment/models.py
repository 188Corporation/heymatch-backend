from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from simple_history.models import HistoricalRecords

from .managers import (
    AppleStoreValidatedReceiptManager,
    PlayStoreValidatedReceiptManager,
)

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
    orderId = models.CharField(max_length=48, unique=True)
    packageName = models.CharField(max_length=48)
    productId = models.CharField(max_length=48)
    quantity = models.IntegerField()
    purchaseToken = models.TextField(max_length=250)

    # Verification result
    purchaseTimeMillis = models.CharField(max_length=32)
    purchaseState = models.IntegerField()
    consumptionState = models.IntegerField()
    # if prod, this field does not exist
    purchaseType = models.IntegerField(null=True, blank=True, default=None)
    acknowledgementState = models.IntegerField(null=True, blank=True)
    kind = models.CharField(max_length=48, null=True, blank=True)
    regionCode = models.CharField(max_length=8, null=True, blank=True)

    objects = PlayStoreValidatedReceiptManager()


class AppleStoreValidatedReceipt(models.Model):
    # receipt info
    product_id = models.CharField(max_length=48)
    transaction_id = models.CharField(max_length=48, unique=True)
    original_transaction_id = models.CharField(max_length=48)
    quantity = models.IntegerField()
    status = models.IntegerField(null=True, blank=True)

    # date
    receipt_creation_date_ms = models.CharField(max_length=32, null=True, blank=True)
    request_date_ms = models.CharField(max_length=32, null=True, blank=True)
    purchase_date_ms = models.CharField(max_length=32, null=True, blank=True)
    original_purchase_date_ms = models.CharField(max_length=32, null=True, blank=True)

    # etc
    is_trial_period = models.BooleanField(null=True, blank=True)
    in_app_ownership_type = models.CharField(max_length=32, null=True, blank=True)
    environment = models.CharField(max_length=32, null=True, blank=True)

    objects = AppleStoreValidatedReceiptManager()


class UserPurchase(models.Model):
    """
    Stores validated receipt, and point or subscription purchased item info.
    """

    class PlatformChoices(models.TextChoices):
        ANDROID = "android"
        IOS = "ios"

    id = models.UUIDField(
        primary_key=True, blank=False, null=False, editable=False, default=uuid4
    )
    user = models.ForeignKey(
        User,
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name="user_purchases",
    )
    platform = models.CharField(
        null=False, blank=False, choices=PlatformChoices.choices, max_length=8
    )
    play_store_receipt = models.ForeignKey(
        PlayStoreValidatedReceipt,
        null=True,
        blank=True,
        default=None,
        on_delete=models.PROTECT,
    )
    apple_store_receipt = models.ForeignKey(
        AppleStoreValidatedReceipt,
        null=True,
        blank=True,
        default=None,
        on_delete=models.PROTECT,
    )
    point_item = models.ForeignKey(
        PointItem,
        null=True,
        blank=True,
        default=None,
        on_delete=models.PROTECT,
    )
    free_pass_item = models.ForeignKey(
        FreePassItem,
        null=True,
        blank=True,
        default=None,
        on_delete=models.PROTECT,
    )
    purchase_processed = models.BooleanField(default=False)  # add up jelly etc
    purchased_at = models.DateTimeField(auto_now_add=True)

    # History
    history = HistoricalRecords()


class UserPointConsumptionHistory(models.Model):
    class ConsumedReasonChoice(models.TextChoices):
        SEND_MATCH_REQUEST = "SEND_MATCH_REQUEST"
        OPENED_PROFILE_PHOTO = "OPENED_PROFILE_PHOTO"

    user = models.ForeignKey(
        User,
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name="user_point_consumption_history",
    )
    consumed_point = models.IntegerField(blank=False, null=False)
    consumed_reason = models.CharField(
        blank=False, null=False, choices=ConsumedReasonChoice.choices, max_length=128
    )
    consumed_at = models.DateTimeField(auto_now_add=True)
