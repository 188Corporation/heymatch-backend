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
    path("auth/", include("heythere.apps.authen.urls")),
    path("users/", include("heythere.apps.user.urls")),
    path("groups/", include("heythere.apps.group.urls")),
    path("hotplaces/", include("heythere.apps.hotplace.urls")),
    path("match/", include("heythere.apps.match.urls")),
]
urlpatterns += router.urls
