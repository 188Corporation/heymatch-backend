from rest_framework import serializers

from heythere.apps.group.models import Group
from heythere.apps.match.models import MatchRequest
from heythere.apps.user.models import User


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


class MatchRequestSendSerializer(serializers.ModelSerializer):
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
        method_name="get_stream_chat_channel"
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

    def get_stream_chat_channel(self, mr: MatchRequest):
        channel = self.context["stream_chat_channel"]
        return dict(id=channel.id, type=channel.type)


class MatchRequestSendBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchRequest
        fields = ()


class MatchedGroupLeaderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "is_group_leader"]
