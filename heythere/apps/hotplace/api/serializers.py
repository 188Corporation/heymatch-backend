from rest_framework import serializers

from heythere.apps.group.models import Group
from heythere.apps.hotplace.models import HotPlace


class HotPlaceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotPlace
        fields = "__all__"


class HotPlaceGroupSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "gps_geoinfo",
            "member_number",
            "member_avg_age",
            "title",
        ]
