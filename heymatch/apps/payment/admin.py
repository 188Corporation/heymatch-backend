from django.contrib import admin

from .models import FreePassItem, PointItem


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
