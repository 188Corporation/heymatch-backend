from django.urls import path

from .api.views import StreamTokenViewSet

app_name = "stream"

stream_token_generate_view = StreamTokenViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    # Token provider
    path("token/", stream_token_generate_view, name="stream-user-token-generate"),
    # Chat app
    path("chat/", stream_token_generate_view, name="stream-user-token-generate"),
]
