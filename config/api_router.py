from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter
from phone_verify.api import VerificationViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

app_name = "api"

router.register('phone', VerificationViewSet, basename='phone')

urlpatterns = [
    path("users/", include("heythere.apps.users.urls")),
]
urlpatterns += router.urls
