from typing import List, Sequence

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
        group.is_active = True
        group.save(using=self._db)
        return group

    def register_user(
        self, group, user: User, is_group_leader: bool = False
    ) -> User or None:
        if not user.is_active:
            user.joined_group = None
            user.save()
            raise RuntimeError("User should be active. Aborting..")
        user.is_group_leader = False
        if is_group_leader:
            user.is_group_leader = True
        user.joined_group = group
        user.save()
        return user

    def register_group_leader_user(self, group, user: User) -> User or None:
        return self.register_user(group, user, is_group_leader=True)

    def register_normal_users(self, group, users: List[User]) -> Sequence[User] or None:
        """
        Note that group_leader should be explicitly registered!
        :return:
        """
        result = []
        saved_users = []
        for user in users:
            try:
                result.append(self.register_user(group, user, is_group_leader=False))
            except RuntimeError:
                # If one of users fails to join, fall back all.
                for saved_u in saved_users:
                    saved_u.joined_group = None
                    saved_u.is_group_leader = False
                    saved_u.save()
                raise RuntimeError(
                    "One of users is inactive. All users should be active. Rolling back all.."
                )
            saved_users.append(user)
        for user in result:
            user.save()
        return result
