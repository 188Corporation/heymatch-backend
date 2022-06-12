from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StreamAppConfig(AppConfig):
    name = "heythere.apps.stream"
    verbose_name = _("StreamIO App")
