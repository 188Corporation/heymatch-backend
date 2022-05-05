from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Avg
from django.db.models.query import QuerySet

from heythere.utils.util import calculate_age_from_birthdate


class UserManager(BaseUserManager):
    def _create_user(self, username: str, phone_number: str, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        user = self.model(username=username, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, username: str, phone_number: str, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, phone_number, password, **extra_fields)

    def create_superuser(
        self, username: str, phone_number: str, password, **extra_fields
    ):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self._create_user(username, phone_number, password, **extra_fields)


class ActiveUserManager(UserManager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(is_active=True)

    def get_group_members(self, group) -> QuerySet:
        return self.get_queryset().filter(joined_group__id=group.id)

    def count_group_members(self, group):
        return self.get_group_members(group).count()

    def count_group_members_avg_age(self, group) -> int or None:
        qs = self.get_group_members(group)
        if qs.count() == 0:
            return None
        return int(qs.aggregate(Avg("age"))["age__avg"])

    def create(self, **kwargs):
        user = self.model(**kwargs)
        # calculate post-creation fields
        if user.birthdate:
            user.age = calculate_age_from_birthdate(user.birthdate)
        user.save(using=self._db)
        return user
