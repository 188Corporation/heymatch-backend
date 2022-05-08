from rest_framework import serializers

from heythere.apps.group.models import Group


class GroupRegisterStep1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
        ]


class GroupRegisterStep2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id"]


class GroupRegisterStep3Serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id"]


class GroupRegisterStep4Serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id"]
