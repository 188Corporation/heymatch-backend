from rest_framework import serializers

from heymatch.apps.group.models import Group
from heymatch.apps.hotplace.models import HotPlace


class HotPlaceNearestBodySerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=10, decimal_places=7)
    long = serializers.DecimalField(max_digits=10, decimal_places=7)


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
            # "member_number",
            # "member_avg_age",
            "title",
        ]
