from django.contrib import admin

from .models import HotPlace


@admin.register(HotPlace)
class HotPlaceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        # "zone_color",
        "is_active",
        "zone_center_geoinfo",
        "zone_boundary_geoinfos",
        "zone_boundary_geoinfos_for_fake_chat",
    ]
    search_fields = [
        "id",
        "name",
        "is_active",
    ]
