from django.urls import path

from heythere.apps.match.api.views import (
    MatchedGroupLeaderDetailViewSet,
    MatchRequestControlViewSet,
    MatchRequestReceivedViewSet,
    MatchRequestSentViewSet,
)

app_name = "match"

match_request_sent_list_view = MatchRequestSentViewSet.as_view({"get": "list"})
match_request_sent_detail_view = MatchRequestSentViewSet.as_view({"get": "retrieve"})
match_request_received_list_view = MatchRequestReceivedViewSet.as_view({"get": "list"})
match_request_received_detail_view = MatchRequestReceivedViewSet.as_view(
    {"get": "retrieve"}
)
match_request_send_to_group_view = MatchRequestControlViewSet.as_view({"post": "send"})
match_request_accept_from_group_view = MatchRequestControlViewSet.as_view(
    {"post": "accept"}
)
match_matched_group_leader_detail_view = MatchedGroupLeaderDetailViewSet.as_view(
    {"get": "retrieve"}
)

urlpatterns = [
    # MatchRequest Sent
    path("request/sent/", match_request_sent_list_view, name="match-request-sent-list"),
    path(
        "request/sent/<str:request_uuid>/",
        match_request_sent_detail_view,
        name="match-request-sent-detail",
    ),
    # MatchRequest Received
    path(
        "request/received/",
        match_request_received_list_view,
        name="match-request-received-list",
    ),
    path(
        "request/received/<str:request_uuid>/",
        match_request_received_detail_view,
        name="match-request-received-detail",
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
        "matched/group/<int:group_id>/group_leader/",
        match_matched_group_leader_detail_view,
        name="match-matched-group-leader-detail",
    ),
]
