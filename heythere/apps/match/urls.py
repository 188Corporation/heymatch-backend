from django.urls import path

from heythere.apps.match.api.views import MatchRequestSentViewSet

app_name = "match"

match_request_sent_list_view = MatchRequestSentViewSet.as_view({"get": "list"})
match_request_sent_detail_view = MatchRequestSentViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("request/sent/", match_request_sent_list_view, name="match-request-sent-list"),
    path(
        "request/sent/<str:request_uuid>/",
        match_request_sent_detail_view,
        name="match-request-sent-detail",
    ),
    # path("request/received/", match_request_sent_list_view, name="match-request-received-list"),
    # path("request/received/<str:request_uuid>/", "TODO", name="match-request-received-detail"),
    #
    # path("request/group/<int:group_id>/send/", "TODO", name="match-request-group-send"),
    # path("request/group/<int:group_id>/accept/", "TODO", name="match-request-group-accept"),
]
