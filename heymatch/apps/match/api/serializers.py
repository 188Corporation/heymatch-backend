from rest_framework import serializers

from heymatch.apps.group.models import Group
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.user.models import User


class MatchRequestListSerializer(serializers.Serializer):
    received = serializers.SerializerMethodField()
    sent = serializers.SerializerMethodField()

    def get_received(self):
        pass

    def get_sent(self):
        pass


# ====================================
# LEGACY
# ====================================
class SimpleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
        ]


class MatchRequestSentSerializer(serializers.ModelSerializer):
    receiver = SimpleGroupSerializer(read_only=True)

    class Meta:
        model = MatchRequest
        fields = [
            "uuid",
            "receiver",
            "unread",
            "accepted",
            "denied",
        ]


class MatchRequestReceivedSerializer(serializers.ModelSerializer):
    sender = SimpleGroupSerializer(read_only=True)

    class Meta:
        model = MatchRequest
        fields = [
            "uuid",
            "sender",
            "unread",
            "accepted",
            "denied",
        ]


class MatchRequestDetailSerializer(serializers.ModelSerializer):
    receiver = SimpleGroupSerializer(read_only=True)
    sender = SimpleGroupSerializer(read_only=True)

    class Meta:
        model = MatchRequest
        fields = [
            "uuid",
            "receiver",
            "sender",
            "unread",
            "accepted",
            "denied",
        ]


class MatchRequestAcceptSerializer(serializers.ModelSerializer):
    receiver = SimpleGroupSerializer(read_only=True)
    sender = SimpleGroupSerializer(read_only=True)
    stream_chat_channel = serializers.SerializerMethodField(
        method_name="get_stream_channel"
    )

    class Meta:
        model = MatchRequest
        fields = [
            "uuid",
            "receiver",
            "sender",
            "unread",
            "accepted",
            "denied",
            "stream_chat_channel",
        ]

    def get_stream_channel(self, mr: MatchRequest):
        channel = self.context["stream_channel_info"]
        return dict(id=channel["id"], cid=channel["cid"], type=channel["type"])


class MatchRequestSendBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchRequest
        fields = ()


class MatchedGroupLeaderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "is_group_leader"]
