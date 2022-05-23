from rest_framework import serializers

from heythere.apps.match.models import MatchRequest


class MatchRequestSentSerializer(serializers.ModelSerializer):
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


class MatchRequestReceivedSerializer(serializers.ModelSerializer):
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
