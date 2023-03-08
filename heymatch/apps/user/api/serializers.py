from rest_framework import serializers

from heymatch.apps.group.api.serializers import FullGroupProfileSerializer
from heymatch.apps.payment.api.serializers import SimpleUserPurchaseSerializer
from heymatch.apps.user.models import (
    AppInfo,
    DeleteScheduledUser,
    User,
    UserProfileImage,
)


class UserProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileImage
        fields = [
            "is_main",
            "status",
            "image",
            "image_blurred",
            "thumbnail",
            "thumbnail_blurred",
            "order",
            "is_active",
        ]


class UserWithGroupFullInfoSerializer(serializers.ModelSerializer):
    user_profile_images = UserProfileImageSerializer(
        "user_profile_images", many=True, read_only=True
    )
    joined_group = FullGroupProfileSerializer(read_only=True)
    user_purchases = SimpleUserPurchaseSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = [
            "id",
            "stream_token",
            "is_first_signup",
            "username",
            "phone_number",
            # "age",
            "gender",
            "birthdate",
            "height_cm",
            "male_body_form",
            "female_body_form",
            "final_education",
            "school_name",
            "is_school_verified",
            "job_title",
            "company_name",
            "is_company_verified",
            "point_balance",
            "user_purchases",
            "free_pass",
            "free_pass_active_until",
            "user_profile_images",
            "joined_group",
            "agreed_to_terms",
        ]

    def to_representation(self, instance: User):
        representation = super().to_representation(instance)
        joined_group = representation["joined_group"]
        user_purchases = representation["user_purchases"]
        del representation["joined_group"]
        del representation["user_purchases"]
        return {
            "user": representation,
            "joined_group": joined_group,
            "user_purchases": user_purchases,
        }


class UserInfoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "gender",
            "birthdate",
            "height_cm",
            "male_body_form",
            "female_body_form",
            # "workplace",
            # "school",
            "agreed_to_terms",
        ]


class UserInfoUpdateBodyRequestSerializer(serializers.ModelSerializer):
    main_profile_image = serializers.ImageField(
        required=False, allow_empty_file=False, use_url=False
    )
    other_profile_image_1 = serializers.ImageField(
        required=False, allow_empty_file=False, use_url=False
    )
    other_profile_image_2 = serializers.ImageField(
        required=False, allow_empty_file=False, use_url=False
    )

    class Meta:
        model = User
        fields = [
            "gender",
            "birthdate",
            "height_cm",
            "male_body_form",
            "female_body_form",
            "final_education",
            "school_name",
            # "is_school_verified",
            "job_title",
            "company_name",
            # "is_company_verified",
            "agreed_to_terms",
            "main_profile_image",
            "other_profile_image_1",
            "other_profile_image_2",
        ]


class DeleteScheduledUserRequestBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeleteScheduledUser
        fields = ["delete_reason"]


class DeleteScheduledUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeleteScheduledUser
        fields = "__all__"


class AppInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppInfo
        fields = "__all__"
