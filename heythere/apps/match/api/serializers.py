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


class MatchRequestSentListSerializer(serializers.ModelSerializer):
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


class MatchRequestSentDetailSerializer(serializers.ModelSerializer):
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


class MatchRequestReceivedListSerializer(serializers.ModelSerializer):
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


class MatchRequestReceivedDetailSerializer(serializers.ModelSerializer):
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


class MatchRequestControlSerializer(serializers.ModelSerializer):
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
