from typing import Sequence

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.query import QuerySet

User = get_user_model()


class ActiveGroupManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(is_active=True)

    def create(self, **kwargs):
        # first create empty Group
        group = self.model(**kwargs)
        group.save(using=self._db)
        return group

    def register_users(self, group, users: Sequence[User]):
        buffer = []
        for i, user in enumerate(users):
            if not user.is_active:
                user.joined_group = None
                user.save()
                raise RuntimeError("All users should be active. Aborting..")
            if i == 0:
                user.is_group_leader = True
            user.joined_group = group
            buffer.append(user)

        for user in buffer:
            user.save()
