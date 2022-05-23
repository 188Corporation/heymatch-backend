from django.contrib.auth import get_user_model
from rest_framework import serializers


class SenderReceiverSerializer(serializers.ModelSerializer):
    """
    This serializer overrides the existing SenderReceiverSerializer of django-messages-drf.
    Refer:
     - django_messages_drf/serializers.py for more detail
     - https://tarsil.github.io/django-messages-drf/settings/
    """

    is_user = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = self.context.get("user")

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "is_user")

    def get_is_user(self, instance):
        return instance.pk == self.user.pk
