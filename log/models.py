from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender, BartenderShift
from web.models import TimeStampedModel


class LogBase(TimeStampedModel):
    manager = models.ForeignKey(
        Bartender,
        on_delete=models.CASCADE,
        related_name="manager",
        verbose_name=_("Bestyrer"),
    )
    licensee = models.ForeignKey(
        Bartender,
        on_delete=models.CASCADE,
        related_name="licensee",
        verbose_name=_("Bevillingshaver"),
    )
    key_figures = models.ManyToManyField(
        Bartender,
        max_length=5,
        blank=True,
        related_name="key_figures",
        verbose_name=_("Foreningens nøglepersoner"),
    )
    purpose = models.TextField(
        max_length=255,
        verbose_name=_("Foreningens formål"),
    )
    representative = models.CharField(
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
        Bartender,
        on_delete=models.CASCADE,
        related_name="loan_agreement",
        verbose_name=_("Låneaftale udfyldt af"),
    )

    class Meta:
        ordering = ("created_at",)
        verbose_name = _("Logbogsskabelon")
        verbose_name_plural = _("Logbogsskabeloner")

    def __str__(self):
        return f"{self.created_at.date()}: Bestyrer: {self.manager}, Bevillingshaver: {self.licensee}"


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
        verbose_name=_("Lokale"),
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=_("Afvigelser fra det normale"),
    )
    police_contacted = models.BooleanField(
        default=False,
        verbose_name=_("Politi kontaktet"),
    )
    fire_authority_contacted = models.BooleanField(
        default=False,
        verbose_name=_("Brandmyndigheder kontaktet"),
    )
    medic_contacted = models.BooleanField(
        default=False,
        verbose_name=_("Ambulance/læge kontaktet"),
    )
    au_personnel_contacted = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("AU-personale kontaktet og/eller tilkaldt"),
    )
    damages = models.TextField(
        max_length=400,
        blank=True,
        verbose_name=_("Skader"),
    )
    collective_evaluation = models.TextField(
        max_length=400,
        blank=True,
        verbose_name=_("Samlet vurdering af arrangementet"),
    )

    class Meta:
        ordering = ("-bartender_shift",)
        verbose_name = _("Logbog")
        verbose_name_plural = _("Logbøger")

    def __str__(self):
        return f"{self.bartender_shift.start_datetime.date()}: {self.bartender_shift.responsible.name}"

    @property
    def short_description(self):
        return truncatechars(self.description, 50)
