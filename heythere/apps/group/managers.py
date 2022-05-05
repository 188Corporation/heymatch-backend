from django.db import models
from django.db.models.query import QuerySet


class ActiveGroupManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(is_active=True)

    def create(self, **kwargs):
        # first create empty Group
        group = self.model(**kwargs)
        group.save(using=self._db)
        return group
