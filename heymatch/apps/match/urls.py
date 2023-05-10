from django.urls import path

from heymatch.apps.match.api.views import MatchRequestViewSet

app_name = "match"

match_request_list_crate_view = MatchRequestViewSet.as_view(
    {"get": "list", "post": "create"}
)
match_request_accept_view = MatchRequestViewSet.as_view({"post": "accept"})
match_request_reject_view = MatchRequestViewSet.as_view({"post": "reject"})
match_request_cancel_view = MatchRequestViewSet.as_view({"post": "cancel"})

urlpatterns = [
    path("", match_request_list_crate_view, name="match-request-list-view"),
    path(
        "<int:match_request_id>/accept/",
        match_request_accept_view,
        name="match-request-accept-view",
    ),
    path(
        "<int:match_request_id>/reject/",
        match_request_reject_view,
        name="match-request-reject-view",
    ),
    path(
        "<int:match_request_id>/cancel/",
        match_request_cancel_view,
        name="match-request-cancel-view",
    ),
]
