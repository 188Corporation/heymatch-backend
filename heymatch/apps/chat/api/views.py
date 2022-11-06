from typing import Any

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.shared.permissions import IsUserJoinedGroup

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
        channels = stream.query_channels(
            {"members": {"$in": [str(request.user.id)]}},
            {"last_message_at": 1},
        )
        return Response(data=channels, status=status.HTTP_200_OK)
