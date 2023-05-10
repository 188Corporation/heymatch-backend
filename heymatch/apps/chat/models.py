from django.contrib.gis.db import models
from django.utils import timezone


class StreamChannel(models.Model):
    # getstream.io channel
    stream_id = models.CharField(
        max_length=255, blank=False, null=False, default=None
    )  # should not conflict with id, so renamed it `stream_id`
    cid = models.CharField(max_length=255, blank=False, null=False, default=None)
    type = models.CharField(max_length=32, blank=False, null=False, default=None)
    group_member = models.ForeignKey(
        "group.GroupMember", null=False, blank=False, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
