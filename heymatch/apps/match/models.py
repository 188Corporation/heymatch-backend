from django.db import models
from django.utils import timezone

from .managers import ActiveStreamChannelManager

MATCH_REQUEST_CHOICES = (
    ("WAITING", "WAITING"),
    ("ACCEPTED", "ACCEPTED"),
    ("REJECTED", "REJECTED"),
    ("CANCELED", "CANCELED"),
)


class MatchRequest(models.Model):
    sender_group = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="match_request_sender_group",
    )
    receiver_group = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="match_request_receiver_group",
    )
    status = models.CharField(
        default=MATCH_REQUEST_CHOICES[0][0],
        choices=MATCH_REQUEST_CHOICES,
        max_length=48,
    )
    created_at = models.DateTimeField(default=timezone.now)

    # getstream.io channel
    stream_channel_id = models.CharField(
        max_length=255, blank=True, null=True, default=None
    )
    stream_channel_cid = models.CharField(
        max_length=255, blank=True, null=True, default=None
    )
    stream_channel_type = models.CharField(
        max_length=32, blank=True, null=True, default=None
    )


# =============
# DEPRECATED
# =============


def stream_channel_default_time():
    return timezone.now() + timezone.timedelta(hours=24)


class StreamChannel(models.Model):
    cid = models.CharField(max_length=255, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    active_until = models.DateTimeField(
        blank=False, null=False
    )  # should be set manually

    objects = models.Manager()
    active_objects = ActiveStreamChannelManager()
