from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UserAppConfig(AppConfig):
    name = "heythere.apps.user"
    verbose_name = _("User App")

    def ready(self):
        try:
            import heythere.apps.users.signals  # noqa F401
        except ImportError:
            pass
