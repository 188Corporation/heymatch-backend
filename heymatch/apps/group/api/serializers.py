from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django_google_maps.fields import GeoPt
from rest_framework import serializers

from heymatch.apps.group.models import (
    Group,
    GroupMember,
    GroupProfileImage,
    GroupV2,
    Recent24HrTopGroupAddress,
    ReportedGroupV2,
)
from heymatch.apps.hotplace.models import HotPlace
from heymatch.apps.user.models import FakeChatUser, User, UserProfileImage
from heymatch.utils.util import (
    generate_rand_geoopt_within_boundary,
    is_geopt_within_boundary,
)


#####################
# Private Serializers
#####################
class _UserProfileByContextSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(
        "decide_whether_original_or_blurred_image"
    )
    thumbnail = serializers.SerializerMethodField(
        "decide_whether_original_or_blurred_thumbnail"
    )

    class Meta:
        model = UserProfileImage
        fields = [
            "is_main",
            "status",
            "image",
            "thumbnail",
            "order",
            "is_active",
        ]

    def decide_whether_original_or_blurred_image(self, obj):
        if self.context.get("force_original_image", False):
            return obj.image.url
        if self.context.get("user_purchased_group_profile_ids", None):
            group_ids = GroupMember.objects.filter(user=obj.user).values_list(
                "group_id", flat=True
            )
            if set(group_ids).intersection(
                set(self.context["user_purchased_group_profile_ids"])
            ):
                return obj.image.url
        return obj.image_blurred.url

    def decide_whether_original_or_blurred_thumbnail(self, obj):
        if self.context.get("force_original_image", False):
            return obj.thumbnail.url
        if self.context.get("user_purchased_group_profile_ids", None):
            group_ids = GroupMember.objects.filter(user=obj.user).values_list(
                "group_id", flat=True
            )
            if set(group_ids).intersection(
                set(self.context["user_purchased_group_profile_ids"])
            ):
                return obj.thumbnail.url
        return obj.thumbnail_blurred.url


class _UserFullFieldSerializer(serializers.ModelSerializer):
    user_profile_images = _UserProfileByContextSerializer(
        "user_profile_images", many=True, read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "gender",
            "birthdate",
            "height_cm",
            "male_body_form",
            "female_body_form",
            "job_title",
            "verified_school_name",
            "verified_company_name",
            "user_profile_images",
        ]


class _GroupMemberSerializer(serializers.ModelSerializer):
    user = _UserFullFieldSerializer(read_only=True)

    class Meta:
        model = GroupMember
        fields = [
            "user",
            "is_user_leader",
        ]


####################
# Public Serializers
####################


class V2GroupLimitedFieldSerializer(serializers.ModelSerializer):
    profile_photo_purchased = serializers.SerializerMethodField(
        "decide_whether_profile_photo_purchased"
    )
    group_members = _GroupMemberSerializer(
        many=True, read_only=True, source="group_member_group"
    )
    about_our_group_tags = serializers.SerializerMethodField(
        "convert_about_our_group_tags_value_to_label",
    )
    meeting_we_want_tags = serializers.SerializerMethodField(
        "convert_meeting_we_want_tags_tags_value_to_label",
    )

    class Meta:
        model = GroupV2
        fields = [
            "id",
            "mode",
            "title",
            "meetup_date",
            "meetup_place_title",
            "meetup_place_address",
            "member_number",
            "member_avg_age",
            "profile_photo_purchased",
            "group_members",
            "about_our_group_tags",
            "meeting_we_want_tags",
            "created_at",
        ]

    def decide_whether_profile_photo_purchased(self, obj):
        if self.context.get("force_original_image", False):
            return True
        if self.context.get("user_purchased_group_profile_ids", None):
            if obj.id in self.context["user_purchased_group_profile_ids"]:
                return True
        return False

    def convert_about_our_group_tags_value_to_label(self, obj):
        refer = {}
        for tag in GroupV2.GroupWhoWeAreTag.choices:
            split = tag[1].split(",")
            refer[tag[0]] = {"value": tag[0], "label": split[0], "color": split[1]}
        result = []
        for tag in obj.about_our_group_tags:
            if tag in refer:
                result.append(refer[tag])
        return result

    def convert_meeting_we_want_tags_tags_value_to_label(self, obj):
        refer = {}
        for tag in GroupV2.GroupWantToMeetTag.choices:
            split = tag[1].split(",")
            refer[tag[0]] = {"value": tag[0], "label": split[0], "color": split[1]}
        result = []
        for tag in obj.meeting_we_want_tags:
            if tag in refer:
                result.append(refer[tag])
        return result


class V2GroupFullFieldSerializer(serializers.ModelSerializer):
    gps_point = serializers.SerializerMethodField()
    group_members = _GroupMemberSerializer(
        many=True, read_only=True, source="group_member_group"
    )
    about_our_group_tags = serializers.SerializerMethodField(
        "convert_about_our_group_tags_value_to_label",
    )
    meeting_we_want_tags = serializers.SerializerMethodField(
        "convert_meeting_we_want_tags_tags_value_to_label",
    )

    def get_gps_point(self, obj):
        return f"{obj.gps_point.x},{obj.gps_point.y}"

    class Meta:
        model = GroupV2
        fields = [
            "id",
            "mode",
            "title",
            "introduction",
            "gps_point",
            "meetup_date",
            "meetup_place_title",
            "meetup_place_address",
            "member_number",
            "member_avg_age",
            "group_members",
            "about_our_group_tags",
            "meeting_we_want_tags",
            "created_at",
        ]

    def convert_about_our_group_tags_value_to_label(self, obj):
        refer = {}
        for tag in GroupV2.GroupWhoWeAreTag.choices:
            split = tag[1].split(",")
            refer[tag[0]] = {"value": tag[0], "label": split[0], "color": split[1]}
        result = []
        for tag in obj.about_our_group_tags:
            if tag in refer:
                result.append(refer[tag])
        return result

    def convert_meeting_we_want_tags_tags_value_to_label(self, obj):
        refer = {}
        for tag in GroupV2.GroupWantToMeetTag.choices:
            split = tag[1].split(",")
            refer[tag[0]] = {"value": tag[0], "label": split[0], "color": split[1]}
        result = []
        for tag in obj.meeting_we_want_tags:
            if tag in refer:
                result.append(refer[tag])
        return result


class V2GroupCreateUpdateSerializer(serializers.ModelSerializer):
    gps_point = serializers.CharField(max_length=120, required=True)

    class Meta:
        model = GroupV2
        fields = [
            "id",
            "title",
            "introduction",
            "gps_point",
            "meetup_date",
            "meetup_place_title",
            "meetup_place_address",
            "member_number",
            "member_avg_age",
            "about_our_group_tags",
            "meeting_we_want_tags",
        ]


class GroupsTopAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recent24HrTopGroupAddress
        fields = [
            "result",
            "aggregated_at",
        ]


class ReportGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportedGroupV2
        fields = [
            "id",
            "reported_group",
            "reported_reason",
            "reported_by",
            "status",
            "created_at",
        ]


class ReportGroupRequestBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportedGroupV2
        fields = ["reported_reason"]


class GroupProfilePhotoPurchaseSerializer(serializers.Serializer):
    from_group_id = serializers.IntegerField()


##################
# Deprecated - V1
##################


class GroupProfileImagesByJoinedGroupConditionSerializer(serializers.ModelSerializer):
    """
    Context "hotplace_id" should be provided from Viewset level.
    If there is hotplace_id, that means user is joined to specific group
    so give out original profile photos conditionally.

    If not, give out blurred profile images.

    If `force_original` is given, then give original image no matter what.

    This serializer handles both cases automatically.
    """

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
        if self.context.get("force_original", False):
            return obj.image.url
        hotplace_id = self.context.get("hotplace_id", None)
        if hotplace_id:
            if obj.group.hotplace.id == hotplace_id:
                return obj.image.url
        return obj.image_blurred.url

    def decide_whether_original_or_blurred_thumbnail(self, obj):
        if self.context.get("force_original", False):
            return obj.thumbnail.url
        hotplace_id = self.context.get("hotplace_id", None)
        if hotplace_id:
            if obj.group.hotplace.id == hotplace_id:
                return obj.thumbnail.url
        return obj.thumbnail_blurred.url


class RestrictedGroupProfileSerializer(serializers.ModelSerializer):
    group_profile_images = GroupProfileImagesByJoinedGroupConditionSerializer(
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
            "match_point",
            "is_active",
            # "active_until",
            "hotplace",
            "group_profile_images",
        ]


class FullGroupProfileSerializer(serializers.ModelSerializer):
    group_profile_images = GroupProfileImagesByJoinedGroupConditionSerializer(
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
            "match_point",
            "is_active",
            # "active_until",
            "hotplace",
            "group_profile_images",
        ]


class RestrictedGroupProfileByHotplaceSerializer(serializers.ModelSerializer):
    groups = RestrictedGroupProfileSerializer("groups", many=True, read_only=True)

    class Meta:
        model = HotPlace
        fields = [
            "id",
            "name",
            "groups",
        ]


class FullGroupProfileByHotplaceSerializer(serializers.ModelSerializer):
    groups = FullGroupProfileSerializer("groups", many=True, read_only=True)

    class Meta:
        model = HotPlace
        fields = [
            "id",
            "name",
            "groups",
        ]


class GroupCreationRequestBodySerializer(serializers.ModelSerializer):
    gps_geoinfo = serializers.CharField(max_length=30)
    group_profile_images = serializers.ImageField(allow_empty_file=False, use_url=False)

    class Meta:
        model = Group
        fields = [
            "gps_geoinfo",
            "title",
            "introduction",
            "male_member_number",
            "female_member_number",
            "member_average_age",
            "group_profile_images",
        ]


class GroupCreationSerializer(serializers.ModelSerializer):
    group_profile_images = serializers.ImageField(allow_empty_file=False, use_url=False)

    class Meta:
        model = Group
        fields = [
            "id",
            "gps_geoinfo",
            "hotplace",
            "title",
            "introduction",
            "male_member_number",
            "female_member_number",
            "member_average_age",
            "group_profile_images",
        ]

    def create(self, validated_data):
        user = validated_data.pop("user")
        gps_geoinfo = validated_data.get("gps_geoinfo")

        # If user is FakeChatUser, replace gps_geoinfo
        try:
            fcu = FakeChatUser.objects.get(user=user)
            validated_data["gps_geoinfo"] = generate_rand_geoopt_within_boundary(
                boundary_geopts=fcu.target_hotplace.zone_boundary_geoinfos_for_fake_chat
            )
            validated_data["hotplace"] = fcu.target_hotplace
        except FakeChatUser.DoesNotExist:
            # Check hotplace inclusiveness
            validated_data["hotplace"] = self.get_hotplace(str(gps_geoinfo))

        # Create Group
        image: InMemoryUploadedFile = validated_data.pop("group_profile_images")
        group = Group.objects.create(**validated_data)
        # Create Group Profile
        GroupProfileImage.objects.create(group=group, image=image)
        # Link group to user
        user.joined_group = group
        user.save()
        return group

    @staticmethod
    def get_hotplace(gps_geoinfo: str) -> HotPlace or None:
        try:
            geopt = GeoPt(gps_geoinfo)
        except ValidationError as e:
            raise serializers.ValidationError(detail=str(e))
        hotplace = None
        for hp in HotPlace.active_objects.all():
            if is_geopt_within_boundary(geopt, hp.zone_boundary_geoinfos):
                hotplace = hp
                break
        if not hotplace:
            raise serializers.ValidationError(detail="헤이매치 핫플 안에 있으셔야 해요! 😯")
        return hotplace

    def to_representation(self, instance: Group):
        serializer = FullGroupProfileSerializer(
            instance=instance, context={"hotplace_id": instance.hotplace.id}
        )
        return serializer.data


class GroupUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "gps_geoinfo",
            "title",
            "introduction",
        ]
