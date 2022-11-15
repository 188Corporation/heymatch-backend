from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.group.api.serializers import RestrictedGroupProfileSerializer
from heymatch.shared.permissions import IsUserJoinedGroup

User = get_user_model()
stream = settings.STREAM_CLIENT


class StreamChatViewSet(viewsets.ModelViewSet):
    """
    getstream.io chat viewset
    Refer: https://getstream.io/chat/docs/react-native/query_channels/?language=python
    """

    permission_classes = [
        IsAuthenticated,
        IsUserJoinedGroup,
    ]
    serializer_class = RestrictedGroupProfileSerializer

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
                "disabled": False,
            },
            sort={"last_message_at": 1},
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
            # find joined group
            target_user = User.objects.get(id=target_user_id)
            target_group = target_user.joined_group
            if not target_group:
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
            serializer_data.append(fresh_data)
        return Response(data=serializer_data, status=status.HTTP_200_OK)
