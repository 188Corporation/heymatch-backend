from django.urls import path

from .api.views import StreamChatViewSet, StreamChatWebHookViewSet

app_name = "chat"

stream_chat_list_viewset = StreamChatViewSet.as_view({"get": "list"})
stream_chat_delete_viewset = StreamChatViewSet.as_view({"delete": "destroy"})
stream_chat_webhook_viewset = StreamChatWebHookViewSet.as_view({"post": "hook"})

urlpatterns = [
    path("webhook/", stream_chat_webhook_viewset, name="stream-chat-webhook-view"),
    path("", stream_chat_list_viewset, name="stream-chat-list-view"),
    path(
        "<str:stream_cid>/",
        stream_chat_delete_viewset,
        name="stream-chat-exit-channel-view",
    ),
]
