from django.contrib import admin

from .models import Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "hotplace",
        "member_number",
        "member_avg_age",
        "gps_geoinfo",
        "gps_checked",
        "gps_last_check_time",
        "title",
        "introduction",
        "desired_other_group_member_number",
        "desired_other_group_member_avg_age_range",
        "register_step_1_completed",
        "register_step_2_completed",
        "register_step_3_completed",
        "register_step_4_completed",
        "register_step_5_completed",
        "is_active",
        "active_until",
    ]
    readonly_fields = [
        "member_number",
        "member_avg_age",
    ]
    search_fields = [
        "id",
        "hotplace",
        "gps_geoinfo",
        "gps_checked",
        "title",
        "introduction",
        "is_active",
        "active_until",
    ]
