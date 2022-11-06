from django.urls import path

from .api.views import StreamChatViewSet

app_name = "chat"

stream_chat_viewset = StreamChatViewSet.as_view({"get": "list"})

urlpatterns = [
    path("", stream_chat_viewset, name="stream-chat-view"),
]
