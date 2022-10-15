from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HotplaceAppConfig(AppConfig):
    name = "heymatch.apps.hotplace"
    verbose_name = _("Hotplace App")
