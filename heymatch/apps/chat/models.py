from django.db import models
from django.utils import timezone


class StreamChannel(models.Model):
    cid = models.CharField(null=False, blank=False, max_length=128)
    # This is the information that is needed for soft-deleted Group
    # We keep provide users chat channels whether they deleted
    # group. In order to keep tracking of group info from Chat list API,
    # we should map User ids with Group ids
    #
    # Data schema
    #   {
    #       "users": [user1.id, user2.id],
    #       "groups": {
    #           "user1.joined_group.id": "user1.id",
    #           "user2.joined_group.id": "user2.id",
    #       }
    #   }
    participants = models.JSONField(null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)
