from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from heymatch.apps.user.forms import UserChangeForm, UserCreationForm

from .models import AppInfo, DeleteScheduledUser, FakeChatUser

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
                    # "birthdate",
                    # "gender",
                    # "height_cm",
                    # "workplace",
                    # "school",
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
                    "joined_group",
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
        # "birthdate",
        # "gender",
        # "height_cm",
        # "workplace",
        # "school",
        "joined_group",
        # "is_group_leader",
        "is_superuser",
        "point_balance",
        "free_pass",
        "free_pass_active_until",
        "is_active",
        "is_deleted",
        "stream_token",
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
        # "birthdate",
        # "gender",
        # "height_cm",
        # "school",
        "joined_group",
        # "is_group_leader",
        "is_superuser",
        "point_balance",
        "free_pass",
        "free_pass_active_until",
        "is_active",
        "is_deleted",
        "stream_token",
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
