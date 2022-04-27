from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MessageAppConfig(AppConfig):
    name = "heythere.apps.message"
    verbose_name = _("Message App")
