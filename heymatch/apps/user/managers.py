from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Q
from django.db.models.query import QuerySet

stream = settings.STREAM_CLIENT


class UserManager(BaseUserManager):
    def _create_user(
        self, phone_number: str, password, username: str = None, **extra_fields
    ):
        """
        Creates and saves a User with the given email and password.
        """
        if username:
            user = self.model(
                phone_number=phone_number, username=username, **extra_fields
            )
        else:
            user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, phone_number: str, password=None, username: str = None, **extra_fields
    ):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, username, **extra_fields)

    def create_superuser(
        self, phone_number: str, password, username: str, **extra_fields
    ):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self._create_user(phone_number, password, username, **extra_fields)


class ActiveUserManager(UserManager):
    """
    Active means: is_active=True AND is_deleted=False
    """

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(Q(is_active=True) & Q(is_deleted=False))

    # def get_group_members(self, group) -> QuerySet:
    #     return self.get_queryset().filter(joined_group__id=group.id)
    #
    # def count_group_members(self, group):
    #     return self.get_group_members(group).count()
    #
    # def count_group_members_avg_age(self, group) -> int or None:
    #     qs = self.get_group_members(group)
    #     if qs.count() == 0:
    #         return None
    #     avg = qs.aggregate(Avg("age"))["age__avg"]
    #     return int(avg) if avg else None

    def create(self, **kwargs):
        user = self.model(**kwargs)
        # Register Stream token
        token = stream.create_token(user_id=str(user.id))
        stream.upsert_user({"id": str(user.id), "role": "user"})
        user.stream_token = token

        # calculate post-creation fields
        # if user.birthdate:
        #     user.age = calculate_age_from_birthdate(user.birthdate)
        user.save(using=self._db)
        return user
