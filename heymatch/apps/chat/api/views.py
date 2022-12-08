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
        is_valid = stream.verify_webhook(request.body, request.META["HTTP_X_SIGNATURE"])

        if not is_valid:
            return Response(
                data="Webhook validation request body is invalid",
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_200_OK)
