from django.contrib.gis.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from .managers import ActiveMatchRequestManager


class MatchRequest(models.Model):
    class MatchRequestStatusChoices(models.TextChoices):
        WAITING = "WAITING"
        ACCEPTED = "ACCEPTED"
        REJECTED = "REJECTED"
        CANCELED = "CANCELED"

    sender_group = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="match_request_sender_group",
    )
    receiver_group = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="match_request_receiver_group",
    )
    status = models.CharField(
        default=MatchRequestStatusChoices.WAITING,
        choices=MatchRequestStatusChoices.choices,
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
    is_deleted = models.BooleanField(blank=False, null=False, default=False)

    # History
    history = HistoricalRecords()

    objects = models.Manager()
    active_objects = ActiveMatchRequestManager()
