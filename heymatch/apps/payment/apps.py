from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaymentAppConfig(AppConfig):
    name = "heymatch.apps.payment"
    verbose_name = _("Payment App")
