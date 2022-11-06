from rest_framework import serializers

from heymatch.apps.group.models import Group
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.user.models import User


class MatchRequestCreateBodySerializer(serializers.Serializer):
    group_id = serializers.IntegerField()


class MatchRequestSerializer(serializers.ModelSerializer):
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


class MatchRequestSendBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchRequest
        fields = ()


class MatchedGroupLeaderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "is_group_leader"]
