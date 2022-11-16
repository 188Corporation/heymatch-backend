from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from .managers import ActiveMatchRequestManager

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

    # Life cycle
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    # History
    history = HistoricalRecords()

    objects = models.Manager()
    active_objects = ActiveMatchRequestManager()
