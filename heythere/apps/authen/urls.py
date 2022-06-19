from django.urls import include, path

from .api.views import StreamTokenViewSet

app_name = "auth"

stream_token_generate_view = StreamTokenViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    # dj-rest-auth
    path("", include("dj_rest_auth.urls")),
    path("signup/", include("dj_rest_auth.registration.urls")),
    path(
        "stream/token/", stream_token_generate_view, name="stream-user-token-generate"
    ),
]
