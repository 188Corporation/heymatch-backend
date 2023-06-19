from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from heymatch.apps.user.forms import UserChangeForm, UserCreationForm

from .models import (
    AppInfo,
    DeleteScheduledUser,
    EmailVerificationCode,
    FakeChatUser,
    UserInvitation,
    UserOnBoarding,
    UserProfileImage,
)

User = get_user_model()


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password", "stream_token")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "phone_number",
                    "birthdate",
                    "gender",
                    "height_cm",
                    "male_body_form",
                    "female_body_form",
                    "job_title",
                    "verified_school_name",
                    "verified_company_name",
                    "is_temp_user",
                    "block_my_school_or_company_users",
                )
            },
        ),
        (
            _("Purchase info"),
            {
                "fields": (
                    "point_balance",
                    "free_pass",
                    "free_pass_active_until",
                )
            },
        ),
        (
            _("Group info"),
            {
                "fields": (
                    # "joined_group",
                    # "is_group_leader",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_deleted",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = [
        "id",
        "username",
        "phone_number",
        # "age",
        "birthdate",
        "gender",
        "height_cm",
        "male_body_form",
        "female_body_form",
        "job_title",
        "verified_school_name",
        "verified_company_name",
        # "joined_group",
        # "is_group_leader",
        "is_superuser",
        "point_balance",
        "free_pass",
        "free_pass_active_until",
        "is_active",
        "is_deleted",
        "stream_token",
        "is_temp_user",
        "invitation_code",
        "block_my_school_or_company_users",
    ]
    history_list_display = [
        "status",
        "last_login",
        "date_joined",
        *list_display,
    ]
    search_fields = [
        "id",
        "username",
        "phone_number",
        # "age",
        "birthdate",
        "gender",
        "height_cm",
        "male_body_form",
        "female_body_form",
        "job_title",
        "verified_school_name",
        "verified_company_name",
        # "joined_group",
        # "is_group_leader",
        "is_superuser",
        "point_balance",
        "free_pass",
        "free_pass_active_until",
        "is_active",
        "is_deleted",
        "stream_token",
        "is_temp_user",
        "invitation_code",
        "block_my_school_or_company_users",
    ]


@admin.register(UserProfileImage)
class UserProfilePhotoAdmin(SimpleHistoryAdmin):
    list_display = [
        "id",
        "user",
        "is_main",
        "status",
        "image",
        "image_blurred",
        "thumbnail",
        "thumbnail_blurred",
        "is_active",
        "order",
    ]
    history_list_display = [*list_display]
    search_fields = [
        "id",
        "user",
        "is_main",
        "status",
        "image",
        "image_blurred",
        "thumbnail",
        "thumbnail_blurred",
        "is_active",
        "order",
    ]


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "email",
        "type",
        "user",
        "code",
        "active_until",
        "is_active",
    ]
    search_fields = [
        "id",
        "email",
        "type",
        "user",
        "code",
        "active_until",
        "is_active",
    ]


@admin.register(UserOnBoarding)
class UserOnBoardingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "basic_info_completed",
        "extra_info_completed",
        "extra_info_in_progress",
        "profile_photo_under_verification",
        "profile_photo_rejected",
        "profile_photo_rejected_reason",
        "onboarding_completed",
    ]
    search_fields = [
        "id",
        "user",
        "basic_info_completed",
        "extra_info_completed",
        "extra_info_in_progress",
        "profile_photo_under_verification",
        "profile_photo_rejected",
        "profile_photo_rejected_reason",
        "onboarding_completed",
    ]


@admin.register(DeleteScheduledUser)
class DeleteScheduledUserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "created_at",
        "delete_schedule_at",
        "delete_reason",
        "status",
    ]
    search_fields = [
        "id",
        "user",
        "created_at",
        "delete_schedule_at",
        "delete_reason",
        "status",
    ]


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "sent",
        "received",
    ]
    search_fields = [
        "id",
        "sent",
        "received",
    ]


@admin.register(FakeChatUser)
class FakeChatUserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "user_phone_number",
        "target_hotplace",
    ]
    search_fields = [
        "id",
        "user",
        "user_phone_number",
        "target_hotplace",
    ]

    def user_phone_number(self, obj):
        return obj.user.phone_number

    user_phone_number.short_description = "Phone Number"


@admin.register(AppInfo)
class AppInfoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "faq_url",
        "terms_of_service_url",
        "privacy_policy_url",
        "terms_of_location_service_url",
        "business_registration_url",
    ]
    search_fields = [
        "id",
        "faq_url",
        "terms_of_service_url",
        "privacy_policy_url",
        "terms_of_location_service_url",
        "business_registration_url",
    ]
