from django.contrib import admin

from .models import (
    AppleStoreValidatedReceipt,
    FreePassItem,
    PlayStoreValidatedReceipt,
    PointItem,
    UserPurchase,
)


@admin.register(PointItem)
class PointItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "product_id",
        "price_in_krw",
        "default_point",
        "bonus_point",
        "krw_per_point",
        "best_deal_check",
    ]
    readonly_fields = [
        "id",
        "product_id",
        "krw_per_point",
    ]
    search_fields = [
        "id",
        "name",
        "product_id",
        "price_in_krw",
        "default_point",
        "bonus_point",
        "krw_per_point",
        "best_deal_check",
    ]


@admin.register(FreePassItem)
class FreePassItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "product_id",
        "price_in_krw",
        "free_pass_duration_in_hour",
        "best_deal_check",
    ]
    readonly_fields = [
        "id",
        "product_id",
    ]
    search_fields = [
        "id",
        "name",
        "product_id",
        "price_in_krw",
        "free_pass_duration_in_hour",
        "best_deal_check",
    ]


@admin.register(PlayStoreValidatedReceipt)
class PlayStoreValidatedReceiptAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "orderId",
        "packageName",
        "productId",
        "quantity",
        "purchaseToken",
        "purchaseTimeMillis",
        "purchaseState",
        "consumptionState",
        "purchaseType",
        "acknowledgementState",
        "kind",
        "regionCode",
    ]
    search_fields = [
        "id",
        "orderId",
        "packageName",
        "productId",
        "quantity",
        "purchaseToken",
        "purchaseTimeMillis",
        "purchaseState",
        "consumptionState",
        "purchaseType",
        "acknowledgementState",
        "kind",
        "regionCode",
    ]


@admin.register(AppleStoreValidatedReceipt)
class AppleStoreValidatedReceiptAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "product_id",
        "transaction_id",
        "original_transaction_id",
        "quantity",
        "status",
        "receipt_creation_date_ms",
        "request_date_ms",
        "purchase_date_ms",
        "original_purchase_date_ms",
        "is_trial_period",
        "in_app_ownership_type",
        "environment",
    ]
    search_fields = [
        "id",
        "product_id",
        "transaction_id",
        "original_transaction_id",
        "quantity",
        "status",
        "receipt_creation_date_ms",
        "request_date_ms",
        "purchase_date_ms",
        "original_purchase_date_ms",
        "is_trial_period",
        "in_app_ownership_type",
        "environment",
    ]


@admin.register(UserPurchase)
class UserPurchaseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "platform",
        "play_store_receipt",
        "apple_store_receipt",
        "point_item",
        "free_pass_item",
        "purchase_processed",
        "purchased_at",
    ]
    history_list_display = ["status", *list_display]
    search_fields = [
        "id",
        "user",
        "platform",
        "play_store_receipt",
        "apple_store_receipt",
        "point_item",
        "free_pass_item",
        "purchase_processed",
        "purchased_at",
    ]
