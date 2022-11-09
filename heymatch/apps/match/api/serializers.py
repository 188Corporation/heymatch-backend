from rest_framework import serializers

from heymatch.apps.group.api.serializers import FullGroupProfileSerializer
from heymatch.apps.match.models import MatchRequest


class MatchRequestCreateBodySerializer(serializers.Serializer):
    group_id = serializers.IntegerField()


class ReceivedMatchRequestSerializer(serializers.ModelSerializer):
    sender_group = FullGroupProfileSerializer(
        "match_request_sender_group", read_only=True
    )

    class Meta:
        model = MatchRequest
        fields = "__all__"
        read_only_fields = [
            "id",
            "sender_group",
            "receiver_group",
            "status",
            "created_at",
            "stream_channel_id",
            "stream_channel_cid",
            "stream_channel_type",
        ]


class SentMatchRequestSerializer(serializers.ModelSerializer):
    receiver_group = FullGroupProfileSerializer(
        "match_request_receiver_group", read_only=True
    )

    class Meta:
        model = MatchRequest
        fields = "__all__"
        read_only_fields = [
            "id",
            "sender_group",
            "receiver_group",
            "status",
            "created_at",
            "stream_channel_id",
            "stream_channel_cid",
            "stream_channel_type",
        ]
