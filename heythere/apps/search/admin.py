from django.contrib import admin

from heythere.apps.search.models import HotPlace


@admin.register(HotPlace)
class HotPlaceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "zone_color", "zone_boundary_info", "geo_test"]
    search_fields = ["id", "name"]
