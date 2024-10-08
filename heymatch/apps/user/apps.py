from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UserAppConfig(AppConfig):
    name = "heymatch.apps.user"
    verbose_name = _("User App")

    def ready(self):
        try:
            import heymatch.apps.user.signals  # noqa F401
        except ImportError:
            pass
