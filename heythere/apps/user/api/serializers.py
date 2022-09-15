from rest_framework import serializers

from heythere.apps.group.api.serializers import JoinedGroupFullInfoSerializer
from heythere.apps.user.models import User


class UserWithGroupFullInfoSerializer(serializers.ModelSerializer):
    joined_group = JoinedGroupFullInfoSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "phone_number",
            "age",
            "birthdate",
            "gender",
            "height_cm",
            "workplace",
            "school",
            "is_group_leader",
            "joined_group",
        ]

    def to_representation(self, instance: User):
        representation = super().to_representation(instance)
        joined_group = representation["joined_group"]
        del representation["joined_group"]
        return {
            "user": representation,
            "joined_group": joined_group,
        }
