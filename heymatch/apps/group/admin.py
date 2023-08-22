from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    Group,
    GroupMember,
    GroupProfileImage,
    GroupProfilePhotoPurchased,
    GroupV2,
    Recent24HrTopGroupAddress,
    ReportedGroupV2,
)


@admin.register(GroupV2)
class GroupV2Admin(SimpleHistoryAdmin):
    list_display = [
        "id",
        "title",
        "introduction",
        "meetup_date",
        "meetup_timerange",
        "meetup_place_title",
        "meetup_place_address",
        "gps_point",
        "gps_address",
        # "gps_geoinfo",
        "member_number",
        "member_avg_age",
        "match_point",
        # "member_avg_height",
        # "member_gender_type",
        "about_our_group_tags",
        "meeting_we_want_tags",
        "created_at",
        "is_active",
    ]
    history_list_display = ["status", *list_display]
    search_fields = [
        "id",
        "title",
        "introduction",
        "meetup_date",
        "meetup_timerange",
        "meetup_place_title",
        "meetup_place_address",
        "gps_point",
        "gps_address",
        # "gps_geoinfo",
        "member_number",
        "member_avg_age",
        "match_point",
        # "member_avg_height",
        # "member_gender_type",
        "about_our_group_tags",
        "meeting_we_want_tags",
        "created_at",
        "is_active",
    ]


@admin.register(GroupMember)
class GroupMemberAdmin(SimpleHistoryAdmin):
    list_display = [
        "id",
        "group",
        "user",
        "is_user_leader",
        "is_active",
    ]
    history_list_display = ["status", *list_display]
    search_fields = [
        "id",
        "group",
        "user",
        "is_user_leader",
        "is_active",
    ]


@admin.register(Recent24HrTopGroupAddress)
class Recent24HrTopGroupAddressAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "result",
        "aggregated_at",
    ]
    search_fields = [
        "id",
        "result",
        "aggregated_at",
    ]


@admin.register(ReportedGroupV2)
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


@admin.register(GroupProfilePhotoPurchased)
class GroupProfilePhotoPurchasedAdmin(SimpleHistoryAdmin):
    list_display = [
        "id",
        "buyer",
        "seller",
    ]
    history_list_display = ["status", *list_display]
    search_fields = [
        "id",
        "buyer",
        "seller",
    ]


# ========================
#  DEPRECATED
# ========================


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
