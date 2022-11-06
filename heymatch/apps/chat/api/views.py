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
            {"members": {"$in": [str(request.user.id)]}},
            {"last_message_at": -1},
        )
        # parse raw data
        serializer_data = []
        for channel in channels["channels"]:
            members = channel["members"]
            target_user_id = None
            for member in members:
                if member["user_id"] != str(request.user.id):
                    target_user_id = str(member["user_id"])
            if not target_user_id:
                continue

            # find joined group
            target_user = User.objects.get(id=target_user_id)
            target_group = target_user.joined_group
            group_serializer = RestrictedGroupProfileSerializer(
                instance=target_group, context={"force_original": True}
            )
            channel["group"] = group_serializer.data

            # delete redundant fields
            del channel["channel"]["config"]
            del channel["channel"]["own_capabilities"]

            serializer_data.append(channel)
        return Response(data=serializer_data, status=status.HTTP_200_OK)
