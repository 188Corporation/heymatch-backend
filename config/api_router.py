from django.conf import settings
from django.urls import include, path
from phone_verify.api import VerificationViewSet
from rest_framework.routers import DefaultRouter, SimpleRouter

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

app_name = "api"

# Register phone SMS verification
router.register("phone", VerificationViewSet, basename="phone")

# Auth and Custom Urls
urlpatterns = [
    path("auth/", include("heythere.apps.authen.urls")),
    path("group/", include("heythere.apps.group.urls")),
    path("search/", include("heythere.apps.search.urls")),
    path("match/", include("heythere.apps.match.urls")),
    path("stream/", include("heythere.apps.stream.urls")),
]
urlpatterns += router.urls
