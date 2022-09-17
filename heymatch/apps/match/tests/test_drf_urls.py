import pytest
from django.urls import resolve, reverse

pytestmark = pytest.mark.django_db


def test_match_request_sent_list():
    assert reverse("api:match:match-request-sent-list") == "/api/match/request/sent/"
    assert (
        resolve("/api/match/request/sent/").view_name
        == "api:match:match-request-sent-list"
    )


def test_match_request_received_list():
    assert (
        reverse("api:match:match-request-received-list")
        == "/api/match/request/received/"
    )
    assert (
        resolve("/api/match/request/received/").view_name
        == "api:match:match-request-received-list"
    )


def test_match_request_send_to_group():
    assert (
        reverse("api:match:match-request-group-send", kwargs={"group_id": 123})
        == "/api/match/request/group/123/send/"
    )
    assert (
        resolve("/api/match/request/group/123/send/").view_name
        == "api:match:match-request-group-send"
    )


def test_match_request_accept_from_group():
    assert (
        reverse("api:match:match-request-group-accept", kwargs={"group_id": 123})
        == "/api/match/request/group/123/accept/"
    )
    assert (
        resolve("/api/match/request/group/123/accept/").view_name
        == "api:match:match-request-group-accept"
    )


def test_match_request_deny_from_group():
    assert (
        reverse("api:match:match-request-group-deny", kwargs={"group_id": 123})
        == "/api/match/request/group/123/deny/"
    )
    assert (
        resolve("/api/match/request/group/123/deny/").view_name
        == "api:match:match-request-group-deny"
    )


def test_group_stream_chat_exit():
    assert (
        reverse("api:match:group-stream-chat-exit", kwargs={"group_id": 123})
        == "/api/match/chat/group/123/exit/"
    )
    assert (
        resolve("/api/match/chat/group/123/exit/").view_name
        == "api:match:group-stream-chat-exit"
    )


def test_match_matched_group_leader_detail_view():
    assert (
        reverse("api:match:match-matched-group-leader-detail", kwargs={"group_id": 123})
        == "/api/match/matched/group/123/group_leader/"
    )
    assert (
        resolve("/api/match/matched/group/123/group_leader/").view_name
        == "api:match:match-matched-group-leader-detail"
    )
