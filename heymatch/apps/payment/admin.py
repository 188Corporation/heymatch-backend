from django.contrib import admin

from .models import FreePassItem, PlayStoreValidatedReceipt, PointItem, UserPurchase


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
        "developerPayload",
        "purchaseType",
        "acknowledgementState",
        "kind",
        "regionCode",
    ]
    readonly_fields = [
        "id",
        "orderId",
        "packageName",
        "productId",
        "quantity",
        "purchaseToken",
        "purchaseTimeMillis",
        "purchaseState",
        "consumptionState",
        "developerPayload",
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
        "developerPayload",
        "purchaseType",
        "acknowledgementState",
        "kind",
        "regionCode",
    ]


@admin.register(UserPurchase)
class UserPurchaseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "platform",
        "play_store_receipt",
        "apple_store_receipt",
        "purchase_processed",
    ]
    readonly_fields = [
        "id",
        "user",
        "platform",
        "play_store_receipt",
        "apple_store_receipt",
        "purchase_processed",
    ]
    search_fields = [
        "id",
        "user",
        "platform",
        "play_store_receipt",
        "apple_store_receipt",
        "purchase_processed",
    ]
