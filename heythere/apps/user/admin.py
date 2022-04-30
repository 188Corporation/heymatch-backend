from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from heythere.apps.user.forms import UserChangeForm, UserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "phone_number",
                    "birth_year",
                    "gender",
                    "height_cm",
                    "workplace",
                    "school",
                )
            },
        ),
        (
            _("Group info"),
            {
                "fields": (
                    "joined_group",
                    "is_group_leader",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = [
        "id",
        "username",
        "phone_number",
        "birthdate",
        "gender",
        "height_cm",
        "workplace",
        "school",
        "joined_group",
        "is_group_leader",
        "is_superuser",
    ]
    search_fields = [
        "id",
        "username",
        "phone_number",
        "birthdate",
        "gender",
        "height_cm",
        "school",
        "joined_group",
        "is_group_leader",
    ]
