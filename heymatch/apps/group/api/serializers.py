from django.core.exceptions import ValidationError
from django.utils import timezone
from django_google_maps.fields import GeoPt
from ordered_model.serializers import OrderedModelSerializer
from psycopg2._range import Range
from rest_framework import serializers

from heymatch.apps.group.models import Group, GroupInvitationCode, GroupProfileImage
from heymatch.apps.hotplace.models import HotPlace
from heymatch.utils.util import is_geopt_within_boundary


class OriginalProfileImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(
        "decide_whether_original_or_blurred_image"
    )
    thumbnail = serializers.SerializerMethodField(
        "decide_whether_original_or_blurred_thumbnail"
    )

    class Meta:
        model = GroupProfileImage
        fields = [
            "image",
            "thumbnail",
        ]

    def decide_whether_original_or_blurred_image(self, obj):
        hotplace_id = self.context.get("hotplace_id")
        if hotplace_id:
            if obj.group.hotplace.id == hotplace_id:
                return obj.image.url
        return obj.image_blurred.url

    def decide_whether_original_or_blurred_thumbnail(self, obj):
        hotplace_id = self.context.get("hotplace_id")
        if hotplace_id:
            if obj.group.hotplace.id == hotplace_id:
                return obj.thumbnail.url
        return obj.thumbnail_blurred.url


class BlurredProfileImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField("change_image_blurred_name")
    thumbnail = serializers.SerializerMethodField("change_thumbnail_blurred_name")

    class Meta:
        model = GroupProfileImage
        fields = [
            "image",
            "thumbnail",
        ]

    def change_image_blurred_name(self, obj):
        return obj.image_blurred.url

    def change_thumbnail_blurred_name(self, obj):
        return obj.thumbnail_blurred.url


class GroupWithBlurredProfileSerializer(serializers.ModelSerializer):
    group_profile_images = BlurredProfileImageSerializer(
        "group_profile_images", many=True, read_only=True
    )

    class Meta:
        model = Group
        fields = [
            "id",
            "gps_geoinfo",
            "title",
            "male_member_number",
            "female_member_number",
            "member_average_age",
            "is_active",
            "active_until",
            "hotplace",
            "group_profile_images",
        ]


class GroupWithOriginalProfileSerializer(serializers.ModelSerializer):
    group_profile_images = OriginalProfileImageSerializer(
        "group_profile_images", many=True, read_only=True
    )

    class Meta:
        model = Group
        fields = [
            "id",
            "gps_geoinfo",
            "title",
            "male_member_number",
            "female_member_number",
            "member_average_age",
            "is_active",
            "active_until",
            "hotplace",
            "group_profile_images",
        ]


class GroupWithBlurredProfileSortedByHotplaceSerializer(serializers.ModelSerializer):
    groups = GroupWithBlurredProfileSerializer("groups", many=True, read_only=True)

    class Meta:
        model = HotPlace
        fields = [
            "id",
            "name",
            "groups",
        ]


class GroupWithOriginalProfileSortedByHotplaceSerializer(serializers.ModelSerializer):
    groups = GroupWithOriginalProfileSerializer("groups", many=True, read_only=True)

    class Meta:
        model = HotPlace
        fields = [
            "id",
            "name",
            "groups",
        ]


class GroupFullInfoSerializer(serializers.ModelSerializer):
    group_profile_images = OriginalProfileImageSerializer(
        "group_profile_images", many=True, read_only=True
    )

    class Meta:
        model = Group
        fields = [
            "id",
            "gps_geoinfo",
            "title",
            "introduction",
            "male_member_number",
            "female_member_number",
            "member_average_age",
            "is_active",
            "active_until",
            "hotplace",
            "group_profile_images",
        ]


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
        validated_data["gps_last_check_time"] = timezone.now()
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


class GroupRegisterStep3PhotoUploadSerializer(serializers.ModelSerializer):
    image_blurred = serializers.ImageField(required=False)
    thumbnail = serializers.ImageField(required=False)
    thumbnail_blurred = serializers.ImageField(required=False)
    order = serializers.IntegerField(required=False)

    class Meta:
        model = GroupProfileImage
        fields = [
            "id",
            "group",
            "image",
            "image_blurred",
            "thumbnail",
            "thumbnail_blurred",
            "order",
        ]

    def create(self, validated_data):
        return GroupProfileImage.objects.create(**validated_data)


class GroupRegisterStep3PhotoUpdateSerializer(OrderedModelSerializer):
    image = serializers.ImageField(required=False)
    image_blurred = serializers.ImageField(required=False)
    thumbnail = serializers.ImageField(required=False)
    thumbnail_blurred = serializers.ImageField(required=False)
    order = serializers.IntegerField(required=False)

    class Meta:
        model = GroupProfileImage
        fields = [
            "id",
            "group",
            "image",
            "image_blurred",
            "thumbnail",
            "thumbnail_blurred",
            "order",
        ]

    def update(self, instance, validated_data):
        order = validated_data.get("order", None)
        if order is not None:
            instance.to(order)
        image = validated_data.get("image", None)
        if image is not None:
            instance.image = image
            instance.save()
        return instance


class GroupRegisterStep3UploadPhotoBodySerializer(serializers.Serializer):
    """
    Body Request Serializer. Not that this will be used in Swagger auto-schema decorator.
    """

    image = serializers.ImageField(allow_empty_file=False, use_url=True)


class GroupRegisterStep3UpdatePhotoBodySerializer(serializers.Serializer):
    """
    Body Request Serializer. Not that this will be used in Swagger auto-schema decorator.
    """

    photo_id = serializers.IntegerField(required=True)
    image = serializers.ImageField(allow_empty_file=False, use_url=True, required=False)
    order = serializers.IntegerField(required=False)


class IntegerRangeField(serializers.Field):
    def to_internal_value(self, data):
        return str(Range(lower=data[0], upper=data[1], bounds="[]"))

    def to_representation(self, value):
        return value


class GroupRegisterStep4Serializer(serializers.ModelSerializer):
    desired_other_group_member_avg_age_range = IntegerRangeField()

    class Meta:
        model = Group
        fields = [
            "id",
            "title",
            "introduction",
            "desired_other_group_member_number",
            "desired_other_group_member_avg_age_range",
        ]


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
