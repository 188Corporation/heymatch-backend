from django.contrib import admin

from .models import Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "hotplace",
        "gps_geo_location",
        "gps_checked",
        "gps_last_check_time",
        "member_number",
        "member_avg_age",
        "title",
        "introduction",
        "desired_other_group_member_number",
        "desired_other_group_member_avg_age_range",
        "is_active",
        "active_until",
    ]
    search_fields = [
        "id",
        "hotplace",
        "gps_geo_location",
        "gps_checked",
        "gps_last_check_time",
        "member_number",
        "member_avg_age",
        "title",
        "introduction",
        "desired_other_group_member_number",
        "desired_other_group_member_avg_age_range",
        "is_active",
        "active_until",
    ]
