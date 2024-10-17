from django.db import models
from django.utils.translation import gettext_lazy as _


class Guide(models.Model):
    class Meta:
        ordering = ("name",)

    GUIDE_TYPES = (
        ("ALL", _("Til alle")),
        ("BT", _("Til bartendere")),
        ("BM", _("Til bestyrelsesmedlemmer")),
    )

    name = models.CharField(max_length=256)
    category = models.CharField(max_length=3, choices=GUIDE_TYPES)
    document = models.FileField(upload_to="guides/")

    def __str__(self):
        return self.name
