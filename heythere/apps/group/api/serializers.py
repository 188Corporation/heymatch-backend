from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone
from django_google_maps.fields import GeoPt
from rest_framework import serializers

from heythere.apps.group.models import Group, GroupInvitationCode, GroupProfileImage
from heythere.apps.search.models import HotPlace
from heythere.apps.user.models import User
from heythere.utils.util import is_geopt_within_boundary


class JoinedGroupStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "gps_geoinfo",
            "gps_checked",
            "gps_last_check_time",
            "register_step_1_completed",
            "register_step_2_completed",
            "register_step_3_completed",
            "register_step_4_completed",
            "register_step_all_confirmed",
            "is_active",
            "active_until",
        ]


class UserJoinedGroupStatusSerializer(serializers.ModelSerializer):
    joined_group = JoinedGroupStatusSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "is_group_leader",
            "joined_group",
        ]

    def to_representation(self, instance: User):
        representation = super().to_representation(instance)
        joined_group = representation["joined_group"]
        del representation["joined_group"]
        return {
            "user_info": representation,
            "joined_group_status": joined_group,
        }


class GroupRegisterStep1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "hotplace",
            "gps_geoinfo",
            "gps_checked",
            "gps_last_check_time",
            "register_step_1_completed",
        ]

    def create(self, validated_data):
        user = validated_data["user"]
        del validated_data["user"]
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
        group = Group.objects.create(**validated_data)

        # Finally, register User as group leader of the Group
        Group.objects.register_group_leader_user(group, user)
        return group

    @staticmethod
    def get_hotplace(gps_geoinfo: str) -> HotPlace or None:
        try:
            geopt = GeoPt(gps_geoinfo)
        except ValidationError as e:
            raise serializers.ValidationError(detail=str(e))

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


class GroupRegisterStep1BodySerializer(serializers.ModelSerializer):
    """
    Body Request Serializer. Not that this will be used in Swagger auto-schema decorator.
    """

    class Meta:
        model = Group
        fields = [
            "gps_geoinfo",
        ]


class GroupRegisterStep2Serializer(serializers.Serializer):
    invitation_codes = serializers.ListField(child=serializers.CharField())

    def perform_invite(self, validated_data, group_leader):
        invitation_codes = validated_data["invitation_codes"]
        group = group_leader.joined_group

        if not group:
            raise serializers.ValidationError(
                "Group leader should create a group first."
            )

        passed = []
        for ic in invitation_codes:
            qs = GroupInvitationCode.active_objects.filter(code=ic)
            if not qs.exists():
                raise serializers.ValidationError("Code does not exist.")
            if not self.is_code_valid(qs.first()):
                raise serializers.ValidationError("Code is not active.")
            passed.append(qs.first())

        # all passed
        for p in passed:
            # join user
            user = p.user
            user.joined_group = group
            user.save()
            # make code inactive
            p.is_active = False
            p.save()

        group.register_step_2_completed = True
        group.save()

    @staticmethod
    def is_code_valid(code: GroupInvitationCode) -> bool:
        return code.is_active and code.active_until > timezone.now()


class GroupRegisterStep2BodySerializer(serializers.Serializer):
    """
    Body Request Serializer. Not that this will be used in Swagger auto-schema decorator.
    """

    invitation_codes = serializers.ListField(child=serializers.CharField())


class GroupRegisterStep3Serializer(serializers.ModelSerializer):
    class Meta:
        model = GroupProfileImage
        fields = ["id", "group", "image"]

    def create(self, validated_data):
        image = GroupProfileImage.objects.create(**validated_data)
        return image


class GroupRegisterStep3BodySerializer(serializers.Serializer):
    """
    Body Request Serializer. Not that this will be used in Swagger auto-schema decorator.
    """

    image = serializers.ImageField(allow_empty_file=False, use_url=True)


class GroupRegisterStep4Serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id"]


class GroupRegisterConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id"]


class GroupInvitationCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInvitationCode
        fields = [
            "code",
            "is_active",
            "active_until",
        ]

    def create(self, validated_data):
        # set previous codes as inactive
        qs = GroupInvitationCode.active_objects.filter(user=validated_data["user"])
        for code in qs:
            code.is_active = False
            code.save()
        invitation_code = GroupInvitationCode.active_objects.create(
            user=validated_data["user"]
        )
        return invitation_code


class GroupInvitationCodeCreateBodySerializer(serializers.ModelSerializer):
    """
    Body Request Serializer. Not that this will be used in Swagger auto-schema decorator.
    """

    class Meta:
        model = GroupInvitationCode
        fields = ()
