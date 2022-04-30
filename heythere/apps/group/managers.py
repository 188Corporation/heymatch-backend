from django.db import models
from django.db.models.query import QuerySet

from heythere.apps.user.models import User


class ActiveGroupManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(is_active=True)

    def create(self, **kwargs):
        # first create empty Group
        group = self.model(**kwargs)

        # calculate post-creation fields
        user_manager = User.active_objects
        group.member_number = user_manager.count_group_members(group)
        group.member_avg_age = user_manager.count_group_members_avg_age(group)
        group.save(using=self._db)
        return group
