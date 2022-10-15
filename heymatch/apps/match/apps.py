from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MatchAppConfig(AppConfig):
    name = "heymatch.apps.match"
    verbose_name = _("Match App")
