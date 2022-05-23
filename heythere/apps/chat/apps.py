from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChatAppConfig(AppConfig):
    name = "heythere.apps.chat"
    verbose_name = _("Chat App")
