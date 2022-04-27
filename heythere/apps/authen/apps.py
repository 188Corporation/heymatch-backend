from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthAppConfig(AppConfig):
    name = "heythere.apps.authen"
    verbose_name = _("Authentication App")
