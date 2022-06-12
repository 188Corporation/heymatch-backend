from django.conf import settings
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from heythere.shared.permissions import IsUserActive

stream = settings.STREAM_CLIENT


class StreamTokenViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for retrieving Token for GetStream User.
    """

    permission_classes = [IsAuthenticated & IsUserActive]

    def retrieve(self, request) -> Response:
        token = stream.create_token(user_id=str(self.request.user.id))
        return Response({"token": token})
