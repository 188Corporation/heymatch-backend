from django.db import models


class Group(models.Model):
    is_active = models.BooleanField(default=True)
    pass
