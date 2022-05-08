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
            "gps_geoinfo",
        ]

    def create(self, validated_data):
        # Determine Hotplace by gps_geoinfo
        gps_geoinfo = validated_data["gps_geoinfo"]
        geopt = GeoPt(gps_geoinfo)

        hotplace = None
        for hp in HotPlace.objects.all():
            boundary_geopts = [GeoPt(geoinfo) for geoinfo in hp.zone_boundary_geoinfos]
            if is_geopt_within_boundary(geopt, boundary_geopts):
                hotplace = hp
                break

        if not hotplace:
            raise serializers.ValidationError(
                detail="Provided GPS geopt does not belong to any hotplaces registered."
            )

        # Save
        validated_data["hotplace"] = hotplace
        validated_data["gps_checked"] = True
        validated_data["gps_last_check_time"] = datetime.now()
        validated_data["register_step_1_completed"] = True
        group = Group.active_objects.create(**validated_data)
        group.save()
        return group


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
