from django.urls import path

from .api.views import (
    TempUserCreateViewSet,
    UsernameUniquenessCheckViewSet,
    UserWithGroupFullInfoViewSet,
)

app_name = "user"

# user_device_register_view = FCMDeviceAuthorizedViewSet.as_view({"post": "create"})
users_my_view = UserWithGroupFullInfoViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "delete": "schedule_delete",
    }
)
users_my_profile_photo_view = UserWithGroupFullInfoViewSet.as_view(
    {
        "delete": "delete_profile_photo",
    }
)
users_unique_name_view = UsernameUniquenessCheckViewSet.as_view({"post": "check"})
users_temp_user_view = TempUserCreateViewSet.as_view({"post": "create"})

urlpatterns = [
    path("my/", users_my_view, name="user-my-detail"),
    path(
        "my/profile/photo/",
        users_my_profile_photo_view,
        name="user-my-profile-photo-delete",
    ),
    path("temp-user/", users_temp_user_view, name="temp-user"),
    path("check-username/", users_unique_name_view, name="user-my-check-username"),
    # path("device/register/", user_device_register_view, name="user_device_register"),
]
