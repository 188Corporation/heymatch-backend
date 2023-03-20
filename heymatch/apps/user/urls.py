from django.urls import path

from .api.views import TempUserCreateViewSet, UserWithGroupFullInfoViewSet

app_name = "user"

# user_device_register_view = FCMDeviceAuthorizedViewSet.as_view({"post": "create"})
users_my_view = UserWithGroupFullInfoViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "delete": "schedule_delete",
    }
)
users_temp_user_view = TempUserCreateViewSet.as_view({"post": "create"})

urlpatterns = [
    path("my/", users_my_view, name="user-my-detail"),
    path("temp-user/", users_temp_user_view, name="temp-user")
    # path("device/register/", user_device_register_view, name="user_device_register"),
]
