from django.db import models
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender, BartenderShift, BoardMember


class LogBase(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Navn"),
    )
    manager = models.ForeignKey(
        BoardMember,
        on_delete=models.CASCADE,
        verbose_name=_("Bestyrer"),
    )
    licensee = models.ForeignKey(
        BoardMember,
        on_delete=models.CASCADE,
        verbose_name=_("Bevillingshaver"),
    )
    key_figures = models.ManyToManyField(
        BoardMember,
        max_length=5,
        blank=True,
        verbose_name=_("Foreningens nøglepersoner"),
    )
    purpose = models.TextField(
        max_length=255,
        verbose_name=_("Foreningens formål"),
    )
    representative = models.ForeignKey(
        max_length=255,
        verbose_name=_("Husrepræsentant"),
    )
    type = models.CharField(
        max_length=255,
        verbose_name=_("Arrangementstype"),
    )
    guests = models.CharField(
        max_length=255,
        verbose_name=_("Forventet antal gæster"),
    )
    loan_agreement = models.ForeignKey(
        BoardMember,
        on_delete=models.CASCADE,
        verbose_name=_("Låneaftale udfyldt af"),
    )


class LogEntry(models.Model):
    template = models.ForeignKey(
        LogBase,
        on_delete=models.CASCADE,
        verbose_name=_("Skabelon"),
    )
    bartender_shift = models.ForeignKey(
        BartenderShift,
        on_delete=models.CASCADE,
        verbose_name=_("Barvagt"),
    )
    location = models.CharField(
        max_length=255,
        verbose_name=_("Lokation"),
    )
    description = models.TextField(
        max_length=500,
        verbose_name=_("Afvigelser fra det normale"),
    )
