from django.urls import path

from .api.views import UserWithGroupFullInfoViewSet

app_name = "user"

# user_device_register_view = FCMDeviceAuthorizedViewSet.as_view({"post": "create"})

urlpatterns = [
    path(
        "my/",
        UserWithGroupFullInfoViewSet.as_view({"get": "retrieve"}),
        name="user-my-detail",
    ),
    path(
        "delete/",
        UserWithGroupFullInfoViewSet.as_view({"post": "schedule_delete"}),
        name="user-schedule-delete",
    ),
    # path("device/register/", user_device_register_view, name="user_device_register"),
]
