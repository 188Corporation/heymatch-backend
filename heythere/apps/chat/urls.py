from django.urls import path
from django_messages_drf.views import (
    InboxListApiView,
    ThreadCRUDApiView,
    ThreadListApiView,
)

app_name = "chat"

urlpatterns = [
    path("inbox/", InboxListApiView.as_view(), name="chat-inbox"),
    path(
        "message/thread/<int:user_id>/send/",
        ThreadCRUDApiView.as_view(),
        name="chat-thread-create",
    ),
    path("message/thread/<str:uuid>/", ThreadListApiView.as_view(), name="chat-thread"),
    path(
        "message/thread/<str:uuid>/<int:user_id>/send/",
        ThreadCRUDApiView.as_view(),
        name="chat-thread-send",
    ),
]
