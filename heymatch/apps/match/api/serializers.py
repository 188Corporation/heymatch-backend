from rest_framework import serializers

from heymatch.apps.group.api.serializers import V2GroupRetrieveSerializer
from heymatch.apps.match.models import MatchRequest


class MatchRequestCreateBodySerializer(serializers.Serializer):
    from_group_id = serializers.IntegerField()
    to_group_id = serializers.IntegerField()


class ReceivedMatchRequestSerializer(serializers.ModelSerializer):
    sender_group = V2GroupRetrieveSerializer(
        "match_request_sender_group",
        read_only=True,
    )

    class Meta:
        model = MatchRequest
        fields = [
            "id",
            "sender_group",
            "status",
            "created_at",
            "stream_channel_id",
            "stream_channel_cid",
            "stream_channel_type",
        ]


class SentMatchRequestSerializer(serializers.ModelSerializer):
    receiver_group = V2GroupRetrieveSerializer(
        "match_request_receiver_group",
        read_only=True,
    )

    class Meta:
        model = MatchRequest
        fields = [
            "id",
            "receiver_group",
            "status",
            "created_at",
            "stream_channel_id",
            "stream_channel_cid",
            "stream_channel_type",
        ]
