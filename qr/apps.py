from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QrConfig(AppConfig):
    name = "qr"
    verbose_name = _("QR-codes")
