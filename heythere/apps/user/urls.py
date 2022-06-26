from django.urls import path
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

app_name = "user"

user_device_register_view = FCMDeviceAuthorizedViewSet.as_view({"post": "create"})

urlpatterns = [
    path("device/register/", user_device_register_view, name="user_device_register"),
]
