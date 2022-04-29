from rest_framework import serializers

from heythere.apps.search.models import HotPlace


class HotPlaceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotPlace
        fields = "__all__"


class HotPlaceListSerializer(HotPlaceDetailSerializer):
    class Meta:
        model = HotPlace
        fields = ["id", "name", "zone_color"]


class GroupsInHotPlaceSerializer(serializers.ModelSerializer):
    pass
