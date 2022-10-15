from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

app_name = "api"

# Auth and Custom Urls
urlpatterns = [
    path("auth/", include("heymatch.apps.authen.urls")),
    path("users/", include("heymatch.apps.user.urls")),
    path("groups/", include("heymatch.apps.group.urls")),
    path("hotplaces/", include("heymatch.apps.hotplace.urls")),
    # path("match/", include("heymatch.apps.match.urls")),
]
urlpatterns += router.urls
