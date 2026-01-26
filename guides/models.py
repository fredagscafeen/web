from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class Guide(models.Model):
    class Meta:
        ordering = ("name",)

    GUIDE_TYPES = (
        ("ALL", _("Til alle")),
        ("BT", _("Til bartendere")),
        ("BM", _("Til bestyrelsesmedlemmer")),
    )
    LANGUAGES = (
        ("da", _("Dansk")),
        ("en", _("Engelsk")),
    )

    name = models.CharField(
        max_length=256,
        verbose_name=_("Name"),
    )
    category = models.CharField(
        max_length=3,
        choices=GUIDE_TYPES,
        verbose_name=_("Kategori"),
    )
    language = models.CharField(
        max_length=2,
        choices=LANGUAGES,
        default="da",
        verbose_name=_("Sprog"),
    )
    document = models.FileField(
        upload_to="guides/",
        verbose_name=_("Dokument"),
    )
    updated_at = models.DateField(
        default=now,
        verbose_name=_("Opdateret"),
    )

    def __str__(self):
        return self.name
