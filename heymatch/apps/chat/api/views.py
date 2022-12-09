import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.chat.models import StreamChannel
from heymatch.apps.group.api.serializers import FullGroupProfileSerializer
from heymatch.apps.group.models import Group
from heymatch.apps.match.models import MatchRequest
from heymatch.shared.permissions import IsUserActive

User = get_user_model()
stream = settings.STREAM_CLIENT
logger = logging.getLogger()
onesignal_client = settings.ONE_SIGNAL_CLIENT


class StreamChatViewSet(viewsets.ModelViewSet):
    """
    getstream.io chat viewset
    Refer: https://getstream.io/chat/docs/react-native/query_channels/?language=python
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
    ]
    serializer_class = FullGroupProfileSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        {
            data: [
                {
                    "group": {
                        "id": ..,
                        "thumbnail":..
                    },
                    "channel": {...},
                    "messages": {...},
                    "pinned_messages": {...},
                    "read": {...},
                    "members": {...}

                }
            ]
        }
        """
        channels = stream.query_channels(
            filter_conditions={
                "members": {"$in": [str(request.user.id)]},
            },
            sort={"last_message_at": -1},
        )
        # parse raw data
        serializer_data = []
        for channel in channels["channels"]:
            fresh_data = {}
            members = channel["members"]
            reads = channel["read"]
            target_user_id = None
            is_last_message_read = True

            # check target user exists
            for member in members:
                if member["user_id"] != str(request.user.id):
                    target_user_id = str(member["user_id"])
            if not target_user_id:
                continue

            # find joined group (can be both active or inactive)
            # StreamChannel.cid can be duplicate. Should give user the latest one
            # so that the group profile is the latest.
            sc = (
                StreamChannel.objects.filter(cid=channel["channel"]["cid"])
                .order_by("-created_at")
                .first()
            )
            target_group_id = None
            for k, v in sc.participants["groups"].items():
                if v == target_user_id:
                    target_group_id = k
            if not target_group_id:
                continue
            try:
                target_group = Group.objects.get(id=target_group_id)
            except Group.DoesNotExist:
                continue

            # check unread or read
            for read in reads:
                if read["user"]["id"] == str(request.user.id):
                    is_last_message_read = (
                        False if read["unread_messages"] > 0 else True
                    )
            # add group info
            group_serializer = self.get_serializer(
                instance=target_group, context={"force_original": True}
            )
            fresh_data["group"] = group_serializer.data
            fresh_data["channel"] = {
                "cid": channel["channel"]["cid"],
                "last_message": {
                    "content": channel["messages"][-1]["text"],
                    "sent_at": channel["messages"][-1]["created_at"],
                    "is_read": is_last_message_read,
                }
                if len(channel["messages"]) > 0
                else None,
            }
            # serialize
            if len(channel["messages"]) == 0:
                serializer_data.insert(0, fresh_data)
            else:
                serializer_data.append(fresh_data)
        return Response(data=serializer_data, status=status.HTTP_200_OK)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # check if Payload's cid is user's or not
        sc = StreamChannel.objects.filter(
            cid=kwargs["stream_cid"]
        ).first()  # there can be multiple

        users = sc.participants["users"]
        if str(request.user.id) not in users:
            raise PermissionDenied("You are not owner of stream channel.")

        # soft-delete channel
        stream.delete_channels(cids=[sc.cid])

        # Get other user.id
        other_user_id = users.remove(str(request.user.id))

        # Deactivate any MatchRequests (there can be multiple since other user of group can
        # delete the previous group and make new one.
        scs = StreamChannel.objects.filter(
            participants__users__contains=[other_user_id, str(request.user.id)]
        )
        for sc in scs:
            group1_id = list(sc.participants["groups"])[0]
            group2_id = list(sc.participants["groups"])[1]

            MatchRequest.active_objects.filter(
                Q(sender_group_id=int(group1_id)) & Q(receiver_group_id=int(group2_id))
            ).update(is_active=False)
            MatchRequest.active_objects.filter(
                Q(sender_group_id=int(group2_id)) & Q(receiver_group_id=int(group1_id))
            ).update(is_active=False)

        return Response(status=status.HTTP_200_OK)


class StreamChatWebHookViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def hook(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Webhook Message format
            {
                "type": "message.new",
                "cid": "messaging:!members-9fb-LLVDHrWzp8Y9BJpOJhsyMnzO2F3yzkTjlNeM9Is",
                "channel_id": "!members-9fb-LLVDHrWzp8Y9BJpOJhsyMnzO2F3yzkTjlNeM9Is",
                "channel_type": "messaging",
                "message": {
                    "id": "82ddf881-ace6-4041-a615-c242ea4724c0",
                    "text": "리리",
                    "html": "<p>리리</p>\n",
                    "type": "regular",
                    "user": {
                        "id": "20b39e2e-9aca-4470-8f85-ee6706338c95",
                        "role": "user",
                        "created_at": "2022-12-05T05:19:50.645351Z",
                        "updated_at": "2022-12-05T05:19:50.645351Z",
                        "last_active": "2022-12-09T02:18:00.679971296Z",
                        "banned": False,
                        "online": True,
                    },
                    "attachments": [],
                    "latest_reactions": [],
                    "own_reactions": [],
                    "reaction_counts": {},
                    "reaction_scores": {},
                    "reply_count": 0,
                    "cid": "messaging:!members-9fb-LLVDHrWzp8Y9BJpOJhsyMnzO2F3yzkTjlNeM9Is",
                    "created_at": "2022-12-09T02:18:04.312673Z",
                    "updated_at": "2022-12-09T02:18:04.312673Z",
                    "shadowed": False,
                    "mentioned_users": [],
                    "silent": False,
                    "pinned": False,
                    "pinned_at": None,
                    "pinned_by": None,
                    "pin_expires": None,
                },
                "user": {
                    "id": "20b39e2e-9aca-4470-8f85-ee6706338c95",
                    "role": "user",
                    "created_at": "2022-12-05T05:19:50.645351Z",
                    "updated_at": "2022-12-05T05:19:50.645351Z",
                    "last_active": "2022-12-09T02:18:00.679971296Z",
                    "banned": False,
                    "online": True,
                    "channel_unread_count": 0,
                    "channel_last_read_at": "2022-12-08T16:47:19.687913984Z",
                    "total_unread_count": 0,
                    "unread_channels": 0,
                    "unread_count": 0,
                },
                "watcher_count": 1,
                "created_at": "2022-12-09T02:18:04.331201052Z",
                "members": [
                    {
                        "user_id": "20b39e2e-9aca-4470-8f85-ee6706338c95",
                        "user": {
                            "id": "20b39e2e-9aca-4470-8f85-ee6706338c95",
                            "role": "user",
                            "created_at": "2022-12-05T05:19:50.645351Z",
                            "updated_at": "2022-12-05T05:19:50.645351Z",
                            "last_active": "2022-12-09T02:18:00.679971296Z",
                            "banned": False,
                            "online": True,
                            "channel_last_read_at": "2022-12-08T16:47:19.687913984Z",
                            "total_unread_count": 0,
                            "unread_channels": 0,
                            "unread_count": 0,
                            "channel_unread_count": 0,
                        },
                        "created_at": "2022-12-08T16:41:14.272136Z",
                        "updated_at": "2022-12-08T16:41:14.272136Z",
                        "banned": False,
                        "shadow_banned": False,
                        "role": "member",
                        "channel_role": "channel_member",
                    },
                    {
                        "user_id": "2f4f60ec-fdc2-4551-bd16-1da8056e0862",
                        "user": {
                            "id": "2f4f60ec-fdc2-4551-bd16-1da8056e0862",
                            "role": "user",
                            "created_at": "2022-12-04T19:09:07.009742Z",
                            "updated_at": "2022-12-04T19:09:07.009742Z",
                            "last_active": "2022-12-08T16:53:50.311381402Z",
                            "banned": False,
                            "online": False,
                            "unread_channels": 1,
                            "unread_count": 21,
                            "channel_unread_count": 21,
                            "channel_last_read_at": "2022-12-08T16:41:49.922396672Z",
                            "total_unread_count": 21,
                        },
                        "created_at": "2022-12-08T16:41:14.272136Z",
                        "updated_at": "2022-12-08T16:41:14.272136Z",
                        "banned": False,
                        "shadow_banned": False,
                        "role": "owner",
                        "channel_role": "channel_member",
                    },
                ],
                "message_id": "82ddf881-ace6-4041-a615-c242ea4724c0",
            }
        """
        is_valid = stream.verify_webhook(request.body, request.META["HTTP_X_SIGNATURE"])
        if not is_valid:
            return Response(
                data="Webhook validation request body is invalid",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not request.data:
            return Response(status=status.HTTP_200_OK)

        sender_user_id = request.data["user"]["id"]
        receiver_user_id = None
        is_all_online = True
        for member in request.data["members"]:
            # mark all online False if any of member is offline
            is_all_online = (
                False if not bool(member["user"]["online"]) else is_all_online
            )
            if member["user_id"] != sender_user_id:
                receiver_user_id = member["user_id"]
                break

        if not receiver_user_id:
            return Response(
                data="Could not find webhook message receiver user id",
                status=status.HTTP_404_NOT_FOUND,
            )

        res = onesignal_client.send_notification_to_specific_users(
            title="새로운 매세지가 왔어요!",
            content="새로운 메세지가 왔어요! ",
            user_ids=[receiver_user_id],
        )
        logger.debug(f"OneSignal response for Stream Webhook message: {res}")

        return Response(status=status.HTTP_200_OK)
