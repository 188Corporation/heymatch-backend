from django.urls import path

from heymatch.apps.match.api.views import (
    GroupStreamChatExitViewSet,
    MatchedGroupLeaderDetailViewSet,
    MatchRequestControlViewSet,
    MatchRequestReceivedViewSet,
    MatchRequestSentViewSet,
)

app_name = "match"

match_request_sent_list_view = MatchRequestSentViewSet.as_view({"get": "list"})
match_request_received_list_view = MatchRequestReceivedViewSet.as_view({"get": "list"})
match_request_send_to_group_view = MatchRequestControlViewSet.as_view({"post": "send"})
match_request_accept_from_group_view = MatchRequestControlViewSet.as_view(
    {"post": "accept"}
)
match_request_deny_from_group_view = MatchRequestControlViewSet.as_view(
    {"post": "deny"}
)
group_stream_chat_exit_view = GroupStreamChatExitViewSet.as_view({"post": "exit"})
match_matched_group_leader_detail_view = MatchedGroupLeaderDetailViewSet.as_view(
    {"get": "retrieve"}
)

urlpatterns = [
    path(""),
    # DEPRECATED
    # MatchRequest Sent
    path("request/sent/", match_request_sent_list_view, name="match-request-sent-list"),
    # MatchRequest Received
    path(
        "request/received/",
        match_request_received_list_view,
        name="match-request-received-list",
    ),
    # MatchRequest Send/Accept
    path(
        "request/group/<int:group_id>/send/",
        match_request_send_to_group_view,
        name="match-request-group-send",
    ),
    path(
        "request/group/<int:group_id>/accept/",
        match_request_accept_from_group_view,
        name="match-request-group-accept",
    ),
    path(
        "request/group/<int:group_id>/deny/",
        match_request_deny_from_group_view,
        name="match-request-group-deny",
    ),
    path(
        "chat/group/<int:group_id>/exit/",
        group_stream_chat_exit_view,
        name="group-stream-chat-exit",
    ),
    path(
        "matched/group/<int:group_id>/group_leader/",
        match_matched_group_leader_detail_view,
        name="match-matched-group-leader-detail",
    ),
]
