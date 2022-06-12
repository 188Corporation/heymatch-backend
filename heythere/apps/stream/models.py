from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class StreamChatChannel(models.Model):
    # channel id set by Stream
    id = models.CharField(
        primary_key=True, max_length=256, blank=False, null=False, editable=False
    )
    type = models.CharField(max_length=128, blank=False, null=False)
    is_active = models.BooleanField(default=True)


class StreamChatChannelMember(models.Model):
    # channel id set by Stream
    member = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="stream_chat_channel_member_user",
    )
    channel = models.ForeignKey(
        StreamChatChannel,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="stream_chat_channel_member_channel",
    )
