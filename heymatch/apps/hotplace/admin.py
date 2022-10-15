from django.contrib import admin

from .models import HotPlace


@admin.register(HotPlace)
class HotPlaceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "zone_color",
        "zone_center_geoinfo",
        "zone_boundary_geoinfos",
    ]
    search_fields = ["id", "name"]
