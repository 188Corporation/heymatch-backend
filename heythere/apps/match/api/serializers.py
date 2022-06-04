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
            "title",
            "unread",
            "accepted",
        ]


class MatchRequestSentDetailSerializer(serializers.ModelSerializer):
    receiver = SimpleGroupSerializer(read_only=True)

    class Meta:
        model = MatchRequest
        fields = [
            "uuid",
            "receiver",
            "title",
            "content",
            "unread",
            "accepted",
        ]


class MatchRequestReceivedListSerializer(serializers.ModelSerializer):
    sender = SimpleGroupSerializer(read_only=True)

    class Meta:
        model = MatchRequest
        fields = [
            "uuid",
            "sender",
            "title",
            "unread",
            "accepted",
        ]


class MatchRequestReceivedDetailSerializer(serializers.ModelSerializer):
    sender = SimpleGroupSerializer(read_only=True)

    class Meta:
        model = MatchRequest
        fields = [
            "uuid",
            "sender",
            "title",
            "content",
            "unread",
            "accepted",
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
            "title",
            "content",
            "unread",
            "accepted",
        ]


class MatchRequestSendBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchRequest
        fields = ()


class MatchedGroupLeaderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "is_group_leader"]
