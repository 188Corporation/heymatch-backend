from uuid import uuid4

from django.db import models
from django_messages_drf.utils import AuditModel


class MatchRequest(AuditModel):
    uuid = models.UUIDField(blank=False, null=False, editable=False, default=uuid4)
    sender = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="match_request_sender_group",
    )
    receiver = models.ForeignKey(
        "group.Group",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="match_request_receiver_group",
    )
    title = models.CharField(max_length=150)
    content = models.TextField()
    unread = models.BooleanField(default=True)
    accepted = models.BooleanField(default=False)
