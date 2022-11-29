from django.urls import path

from .api.views import StreamChatViewSet

app_name = "chat"

stream_chat_list_viewset = StreamChatViewSet.as_view({"get": "list"})
stream_chat_delete_viewset = StreamChatViewSet.as_view({"delete": "destroy"})

urlpatterns = [
    path("", stream_chat_list_viewset, name="stream-chat-list-view"),
    path("<str:stream_cid>/", stream_chat_delete_viewset, name="stream-exit-chat"),
]
