from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Group, GroupProfileImage, ReportedGroup


@admin.register(Group)
class GroupAdmin(SimpleHistoryAdmin):
    list_display = [
        "id",
        "hotplace",
        "gps_geoinfo",
        "title",
        "introduction",
        "male_member_number",
        "female_member_number",
        "member_average_age",
        "match_point",
        # "gps_checked",
        # "gps_last_check_time",
        # "member_number",
        # "member_avg_age",
        # "desired_other_group_member_number",
        # "desired_other_group_member_avg_age_range",
        # "active_until",
        "is_active",
        "is_deleted",
    ]
    # readonly_fields = [
    #     "member_number",
    #     "member_avg_age",
    # ]
    history_list_display = ["status", *list_display]
    search_fields = [
        "id",
        "hotplace",
        "gps_geoinfo",
        "title",
        "introduction",
        "male_member_number",
        "female_member_number",
        "member_average_age",
        "match_point",
        "is_active",
        "is_deleted",
    ]


@admin.register(GroupProfileImage)
class GroupProfilePhotoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "group",
        "image",
        "image_blurred",
        "thumbnail",
        "thumbnail_blurred",
        "order",
    ]
    history_list_display = ["status", *list_display]
    search_fields = [
        "id",
        "group",
        "image",
        "image_blurred",
        "thumbnail",
        "thumbnail_blurred",
        "order",
    ]


@admin.register(ReportedGroup)
class ReportedGroupAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "reported_group",
        "reported_reason",
        "reported_by",
        "status",
        "created_at",
    ]
    search_fields = [
        "id",
        "reported_group",
        "reported_reason",
        "reported_by",
        "status",
        "created_at",
    ]


# ========================
#  DEPRECATED
# ========================

# @admin.register(GroupInvitationCode)
# class GroupInvitationCodeAdmin(admin.ModelAdmin):
#     list_display = [
#         "id",
#         "code",
#         "user",
#         "is_active",
#         "active_until",
#     ]
#     search_fields = [
#         "id",
#         "code",
#         "user",
#         "is_active",
#         "active_until",
#     ]

# @admin.register(GroupBlackList)
# class GroupBlackListAdmin(admin.ModelAdmin):
#     list_display = [
#         "id",
#         "group",
#         "blocked_group",
#         "is_active",
#         "active_until",
#     ]
#     search_fields = [
#         "id",
#         "group",
#         "blocked_group",
#         "is_active",
#         "active_until",
#     ]
