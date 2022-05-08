from datetime import datetime

from django_google_maps.fields import GeoPt
from rest_framework import serializers

from heythere.apps.group.models import Group
from heythere.apps.search.models import HotPlace
from heythere.utils.util import is_geopt_within_boundary


class GroupRegisterStep1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            # "hotplace",
            "gps_geoinfo",
            # "gps_checked",
            # "gps_last_check_time",
            # "register_step_1_completed",
        ]

    def create(self, validated_data):
        # Determine Hotplace by gps_geoinfo
        hotplace = self.get_hotplace(validated_data["gps_geoinfo"])
        if not hotplace:
            raise serializers.ValidationError(
                detail="Provided GPS geopt does not belong to any hotplaces registered."
            )

        # Save Group
        validated_data["hotplace"] = hotplace
        validated_data["gps_checked"] = True
        validated_data["gps_last_check_time"] = datetime.now()
        validated_data["register_step_1_completed"] = True
        group = Group.active_objects.create(**validated_data)

        # Finally, register User as group leader of the Group
        Group.active_objects.register_group_leader_user(group, validated_data["user"])
        return group

    @staticmethod
    def get_hotplace(gps_geoinfo: str) -> HotPlace or None:
        geopt = GeoPt(gps_geoinfo)
        hotplace = None
        for hp in HotPlace.objects.all():
            if is_geopt_within_boundary(geopt, hp.zone_boundary_geoinfos):
                hotplace = hp
                break

        if not hotplace:
            raise serializers.ValidationError(
                detail="Provided GPS geopt does not belong to any hotplaces registered."
            )
        return hotplace


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


class GroupRegisterStep5Serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id"]
