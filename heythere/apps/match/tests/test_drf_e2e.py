from typing import List

import pytest
from django.conf import settings
from rest_framework.test import APIClient
from stream_chat.base.exceptions import StreamAPIException

from heythere.apps.group.models import Group, GroupBlackList
from heythere.apps.match.models import MatchRequest
from heythere.apps.user.tests.factories import ActiveUserFactory

pytestmark = pytest.mark.django_db


class TestMatchRequestListEndpoints:
    def test_match_request_sent_list_if_all_good(
        self, active_group: Group, api_client: APIClient
    ):
        active_user = ActiveUserFactory(joined_group=active_group, is_group_leader=True)
        api_client.force_authenticate(user=active_user)

        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert res.data == []

    def test_match_request_sent_list_if_not_authenticated(self, api_client: APIClient):
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 401

    def test_match_request_sent_list_if_not_joined_group(self, api_client: APIClient):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 403

    def test_match_request_sent_list_if_not_group_leader(
        self, active_group: Group, api_client: APIClient
    ):
        active_user = ActiveUserFactory(joined_group=active_group)
        api_client.force_authenticate(user=active_user)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 403

    def test_match_request_received_list_if_all_good(
        self, active_group: Group, api_client: APIClient
    ):
        active_user = ActiveUserFactory(joined_group=active_group, is_group_leader=True)
        api_client.force_authenticate(user=active_user)

        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert res.data == []

    def test_match_request_received_list_if_not_authenticated(
        self, api_client: APIClient
    ):
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 401

    def test_match_request_received_list_if_not_joined_group(
        self, api_client: APIClient
    ):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 403

    def test_match_request_received_list_if_not_group_leader(
        self, active_group: Group, api_client: APIClient
    ):
        active_user = ActiveUserFactory(joined_group=active_group)
        api_client.force_authenticate(user=active_user)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 403


class TestMatchRequestControlEndpoints:
    # -------------
    #  MR Send flow
    # -------------
    def test_match_request_send_to_group_if_all_good(
        self, active_two_groups: List[Group], api_client: APIClient
    ):
        sender_group = active_two_groups[0]
        receiver_group = active_two_groups[1]

        sender = ActiveUserFactory(joined_group=sender_group, is_group_leader=True)
        api_client.force_authenticate(user=sender)

        # check before sending
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 0

        # send MR
        res = api_client.post(f"/api/match/request/group/{receiver_group.id}/send/")
        assert res.status_code == 200

        # check sent list
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 1

        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert len(res.data) == 0

        # check from receiver user
        receiver = ActiveUserFactory(joined_group=receiver_group, is_group_leader=True)
        api_client.force_authenticate(user=receiver)
        # check sent list
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 0

        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert len(res.data) == 1

    def test_match_request_send_to_group_if_not_authenticated(
        self, active_two_groups: List[Group], api_client: APIClient
    ):
        receiver_group = active_two_groups[1]

        # send MR
        res = api_client.post(f"/api/match/request/group/{receiver_group.id}/send/")
        assert res.status_code == 401

    def test_match_request_send_to_group_if_not_joined_group(
        self, active_two_groups: List[Group], api_client: APIClient
    ):
        receiver_group = active_two_groups[1]

        sender = ActiveUserFactory(joined_group=None, is_group_leader=True)
        api_client.force_authenticate(user=sender)

        # send MR
        res = api_client.post(f"/api/match/request/group/{receiver_group.id}/send/")
        assert res.status_code == 403

    def test_match_request_send_to_group_if_not_group_leader(
        self, active_two_groups: List[Group], api_client: APIClient
    ):
        sender_group = active_two_groups[0]
        receiver_group = active_two_groups[1]

        sender = ActiveUserFactory(joined_group=sender_group)
        api_client.force_authenticate(user=sender)

        # send MR
        res = api_client.post(f"/api/match/request/group/{receiver_group.id}/send/")
        assert res.status_code == 403

    def test_match_request_send_to_group_if_twice(
        self, active_two_groups: List[Group], api_client: APIClient
    ):
        sender_group = active_two_groups[0]
        receiver_group = active_two_groups[1]

        sender = ActiveUserFactory(joined_group=sender_group, is_group_leader=True)
        api_client.force_authenticate(user=sender)

        # send MR
        res = api_client.post(f"/api/match/request/group/{receiver_group.id}/send/")
        assert res.status_code == 200

        # send again
        res = api_client.post(f"/api/match/request/group/{receiver_group.id}/send/")
        assert res.status_code == 401

    # ---------------
    #  MR Accept flow
    # ---------------
    def test_match_request_accept_from_group_if_all_good(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        stream = settings.STREAM_CLIENT
        sender = ActiveUserFactory(
            joined_group=match_request.sender, is_group_leader=True
        )
        receiver = ActiveUserFactory(
            joined_group=match_request.receiver, is_group_leader=True
        )
        api_client.force_authenticate(user=receiver)

        assert match_request.unread is True
        assert match_request.accepted is False
        assert match_request.denied is False

        # first upsert user in Stream
        stream.upsert_user({"id": str(sender.id), "role": "user"})
        stream.upsert_user({"id": str(receiver.id), "role": "user"})

        # check list before accepting
        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert len(res.data) == 1

        api_client.force_authenticate(user=sender)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 1

        api_client.force_authenticate(user=sender)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.sender.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["id"] == match_request.receiver.id

        api_client.force_authenticate(user=receiver)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.receiver.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["id"] == match_request.sender.id

        # accept MR
        api_client.force_authenticate(user=receiver)
        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/accept/"
        )
        channel_type = res.data["stream_chat_channel"]["type"]
        channel_id = res.data["stream_chat_channel"]["id"]
        channel_cid = res.data["stream_chat_channel"]["cid"]
        assert settings.STREAM_CHAT_CHANNEL_TYPE == channel_type
        assert "!members-" in channel_id
        assert f"{settings.STREAM_CHAT_CHANNEL_TYPE}:{channel_id}" == channel_cid
        match_request = MatchRequest.objects.get(
            sender=match_request.sender, receiver=match_request.receiver
        )
        assert res.status_code == 200
        assert match_request.unread is False
        assert match_request.accepted is True
        assert match_request.denied is False

        # check list after accepting
        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert len(res.data) == 0

        api_client.force_authenticate(user=sender)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 0

        api_client.force_authenticate(user=sender)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.sender.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["id"] == match_request.receiver.id

        api_client.force_authenticate(user=receiver)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.receiver.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["id"] == match_request.sender.id

        # delete users in Stream
        stream.delete_user(
            str(sender.id),
            mark_messages_deleted=True,
            hard_delete=True,
            delete_conversation_channels=True,
        )
        stream.delete_user(
            str(receiver.id),
            mark_messages_deleted=True,
            hard_delete=True,
            delete_conversation_channels=True,
        )

        # delete channel in Stream
        stream.delete_channels([channel_cid], hard_delete=True)

    def test_match_request_accept_from_group_if_not_authenticated(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/accept/"
        )
        assert res.status_code == 401

    def test_match_request_accept_from_group_if_not_joined_group(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        receiver = ActiveUserFactory(joined_group=None, is_group_leader=True)
        api_client.force_authenticate(user=receiver)

        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/accept/"
        )
        assert res.status_code == 403

    def test_match_request_accept_from_group_if_not_group_leader(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        receiver = ActiveUserFactory(joined_group=match_request.receiver)
        api_client.force_authenticate(user=receiver)

        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/accept/"
        )
        assert res.status_code == 403

    def test_match_request_accept_from_group_if_not_received(
        self, active_group: Group, match_request: MatchRequest, api_client: APIClient
    ):
        receiver = ActiveUserFactory(
            joined_group=match_request.receiver, is_group_leader=True
        )
        api_client.force_authenticate(user=receiver)

        res = api_client.post(f"/api/match/request/group/{active_group.id}/accept/")
        assert res.status_code == 401

    def test_match_request_accept_from_group_if_already_accepted(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        stream = settings.STREAM_CLIENT
        sender = ActiveUserFactory(
            joined_group=match_request.sender, is_group_leader=True
        )
        receiver = ActiveUserFactory(
            joined_group=match_request.receiver, is_group_leader=True
        )
        api_client.force_authenticate(user=receiver)

        # first upsert user in Stream
        stream.upsert_user({"id": str(sender.id), "role": "user"})
        stream.upsert_user({"id": str(receiver.id), "role": "user"})

        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/accept/"
        )
        channel_cid = res.data["stream_chat_channel"]["cid"]
        assert res.status_code == 200

        # Accept again
        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/accept/"
        )
        assert res.status_code == 401

        # delete users in Stream
        stream.delete_user(
            str(sender.id),
            mark_messages_deleted=True,
            hard_delete=True,
            delete_conversation_channels=True,
        )
        stream.delete_user(
            str(receiver.id),
            mark_messages_deleted=True,
            hard_delete=True,
            delete_conversation_channels=True,
        )
        # delete channel in Stream
        stream.delete_channels([channel_cid], hard_delete=True)

    # ---------------
    #  MR Deny flow
    # ---------------
    def test_match_request_deny_from_group_if_all_good(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        sender = ActiveUserFactory(
            joined_group=match_request.sender, is_group_leader=True
        )
        receiver = ActiveUserFactory(
            joined_group=match_request.receiver, is_group_leader=True
        )
        api_client.force_authenticate(user=receiver)

        assert match_request.unread is True
        assert match_request.accepted is False
        assert match_request.denied is False

        # check list before accepting
        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert len(res.data) == 1

        api_client.force_authenticate(user=sender)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 1

        qs = GroupBlackList.active_objects.filter(
            group=receiver.joined_group, blocked_group=sender.joined_group
        )
        assert len(qs) == 0
        qs = GroupBlackList.active_objects.filter(
            group=sender.joined_group, blocked_group=receiver.joined_group
        )
        assert len(qs) == 0

        api_client.force_authenticate(user=sender)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.sender.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["id"] == match_request.receiver.id

        api_client.force_authenticate(user=receiver)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.receiver.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["id"] == match_request.sender.id

        # Deny MR
        api_client.force_authenticate(user=receiver)
        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/deny/"
        )
        match_request = MatchRequest.objects.get(
            sender=match_request.sender, receiver=match_request.receiver
        )
        assert res.status_code == 200
        assert match_request.unread is False
        assert match_request.accepted is False
        assert match_request.denied is True

        qs = GroupBlackList.active_objects.all()
        assert len(qs) == 2
        qs = GroupBlackList.active_objects.filter(
            group=receiver.joined_group, blocked_group=sender.joined_group
        )
        assert len(qs) == 1
        qs = GroupBlackList.active_objects.filter(
            group=sender.joined_group, blocked_group=receiver.joined_group
        )
        assert len(qs) == 1

        # check list after accepting
        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert len(res.data) == 0

        api_client.force_authenticate(user=sender)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 0

        api_client.force_authenticate(user=sender)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.sender.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 0

        api_client.force_authenticate(user=receiver)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.receiver.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 0

    def test_match_request_deny_from_group_if_not_authenticated(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/deny/"
        )
        assert res.status_code == 401

    def test_match_request_deny_from_group_if_not_received(
        self, active_group: Group, match_request: MatchRequest, api_client: APIClient
    ):
        receiver = ActiveUserFactory(
            joined_group=match_request.receiver, is_group_leader=True
        )
        api_client.force_authenticate(user=receiver)

        res = api_client.post(f"/api/match/request/group/{active_group.id}/deny/")
        assert res.status_code == 401

    def test_match_request_deny_from_group_if_already_denied(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        receiver = ActiveUserFactory(
            joined_group=match_request.receiver, is_group_leader=True
        )
        api_client.force_authenticate(user=receiver)

        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/deny/"
        )
        assert res.status_code == 200

        # Deny again
        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/deny/"
        )
        assert res.status_code == 401

    # ----------------------
    #  Stream Chat Exit flow
    # ----------------------
    def test_match_stream_chat_exit_if_all_good(
        self, match_request: MatchRequest, api_client: APIClient
    ):
        stream = settings.STREAM_CLIENT
        sender = ActiveUserFactory(
            joined_group=match_request.sender, is_group_leader=True
        )
        receiver = ActiveUserFactory(
            joined_group=match_request.receiver, is_group_leader=True
        )
        api_client.force_authenticate(user=receiver)

        assert match_request.unread is True
        assert match_request.accepted is False
        assert match_request.denied is False

        # check list before accepting
        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert len(res.data) == 1

        api_client.force_authenticate(user=sender)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 1

        qs = GroupBlackList.active_objects.filter(
            group=receiver.joined_group, blocked_group=sender.joined_group
        )
        assert len(qs) == 0
        qs = GroupBlackList.active_objects.filter(
            group=sender.joined_group, blocked_group=receiver.joined_group
        )
        assert len(qs) == 0

        api_client.force_authenticate(user=sender)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.sender.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["id"] == match_request.receiver.id

        api_client.force_authenticate(user=receiver)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.receiver.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["id"] == match_request.sender.id

        # first upsert user in Stream
        stream.upsert_user({"id": str(sender.id), "role": "user"})
        stream.upsert_user({"id": str(receiver.id), "role": "user"})

        # accept MR
        api_client.force_authenticate(user=receiver)
        res = api_client.post(
            f"/api/match/request/group/{match_request.sender.id}/accept/"
        )
        channel_cid = res.data["stream_chat_channel"]["cid"]

        # exit stream chat
        res = api_client.post(f"/api/match/chat/group/{match_request.sender.id}/exit/")
        assert res.status_code == 200

        qs = GroupBlackList.active_objects.all()
        assert len(qs) == 2
        qs = GroupBlackList.active_objects.filter(
            group=receiver.joined_group, blocked_group=sender.joined_group
        )
        assert len(qs) == 1
        qs = GroupBlackList.active_objects.filter(
            group=sender.joined_group, blocked_group=receiver.joined_group
        )
        assert len(qs) == 1

        # check list after accepting
        res = api_client.get("/api/match/request/received/")
        assert res.status_code == 200
        assert len(res.data) == 0

        api_client.force_authenticate(user=sender)
        res = api_client.get("/api/match/request/sent/")
        assert res.status_code == 200
        assert len(res.data) == 0

        api_client.force_authenticate(user=sender)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.sender.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 0

        api_client.force_authenticate(user=receiver)
        res = api_client.get(
            f"/api/search/hotplace/{match_request.receiver.hotplace.id}/group/"
        )
        assert res.status_code == 200
        assert len(res.data) == 0

        # delete users in Stream
        stream.delete_user(
            str(sender.id),
            mark_messages_deleted=True,
            hard_delete=True,
            delete_conversation_channels=True,
        )
        stream.delete_user(
            str(receiver.id),
            mark_messages_deleted=True,
            hard_delete=True,
            delete_conversation_channels=True,
        )

        # deleting channel should not work
        with pytest.raises(StreamAPIException):
            stream.delete_channels([channel_cid], hard_delete=True)
