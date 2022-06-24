from django.contrib import admin

from .models import Group, GroupBlackList, GroupInvitationCode, GroupProfileImage


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
        "register_step_all_confirmed",
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


@admin.register(GroupInvitationCode)
class GroupInvitationCodeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "code",
        "user",
        "is_active",
        "active_until",
    ]
    search_fields = [
        "id",
        "code",
        "user",
        "is_active",
        "active_until",
    ]


@admin.register(GroupProfileImage)
class GroupProfilePhotoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "group",
        "image",
    ]
    search_fields = [
        "id",
        "group",
        "image",
    ]


@admin.register(GroupBlackList)
class GroupBlackListAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "group",
        "blocked_group",
        "is_active",
        "active_until",
    ]
    search_fields = [
        "id",
        "group",
        "blocked_group",
        "is_active",
        "active_until",
    ]
