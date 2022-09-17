from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GroupAppConfig(AppConfig):
    name = "heymatch.apps.group"
    verbose_name = _("Group App")
