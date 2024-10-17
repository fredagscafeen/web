from django.db import models
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender


class UdlejningCommon(models.Model):
    class Meta:
        abstract = True

    PAYMENT_CHOICES = (
        ("EAN", _("EAN")),
        ("invoice", _("Faktura")),
        ("card", _("Kort i baren")),
    )

    dateFrom = models.DateTimeField(
        verbose_name=_("Start dato & tid"),
        help_text=_("Hvornår skal anlægget afhentes/stilles op?"),
    )
    dateTo = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Slut dato & tid"),
        help_text=_("Hvornår skal anlægget afleveres/pilles ned?"),
    )
    whoReserved = models.CharField(max_length=140, verbose_name=_("Hvem er I?"))

    contactEmail = models.EmailField(verbose_name=_("Email til kontaktperson"))
    contactPhone = models.IntegerField(
        verbose_name=_("Telefonnummer til kontaktperson"), blank=True, null=True
    )

    whoPays = models.CharField(
        max_length=140,
        verbose_name=_("Hvem betaler?"),
        help_text=_(
            "Hvem skal regningen sendes til? (Fulde navn på person, virksomhed eller organisation)"
        ),
    )
    paymentType = models.CharField(
        max_length=140,
        choices=PAYMENT_CHOICES,
        verbose_name=_("Betalingsform"),
        help_text=_("Hvordan bliver der betalt?"),
    )

    EANnumber = models.BigIntegerField(
        verbose_name=_("EAN-nummer"),
        blank=True,
        null=True,
        help_text=_("Skal kun angives, hvis der skal faktureres til et EAN-nummer"),
    )

    where = models.TextField(
        max_length=140,
        verbose_name=_("Lokation"),
        help_text=_("Hvor bliver arrangmentet afholdt?"),
    )
    expectedConsummation = models.TextField(
        max_length=140,
        verbose_name=_("Forventet forbrug"),
        help_text=_(
            "Hvilke slags øl eller andre drikkevarer ønskes der og hvor mange fustager af hver type?"
        ),
    )
    comments = models.TextField(blank=True, verbose_name=_("Kommentarer"))

    def __str__(self):
        return f"{self.dateFrom} {self.whoReserved}"


class Udlejning(UdlejningCommon):
    ASSOCIATION_CHOICES = (
        ("internal", _("Intern")),
        ("external", _("Ekstern")),
    )

    STATUS_CHOICES = (
        ("notsent", _("Regning ikke sendt")),
        ("sent", _("Regning sendt")),
        ("paid", _("Regning betalt")),
    )

    SYSTEM_CHOICES = (
        ("small", _("Lille")),
        ("medium", _("Mellem")),
    )

    draftBeerSystem = models.CharField(
        max_length=16,
        choices=SYSTEM_CHOICES,
        blank=True,
        verbose_name=_("Fadølsanlæg"),
        help_text=_("Hvilket anlæg vil I låne?"),
    )
    association = models.CharField(
        max_length=16,
        choices=ASSOCIATION_CHOICES,
        blank=True,
        verbose_name=_("Tilknytning"),
    )
    actualConsummation = models.TextField(
        max_length=140, blank=True, verbose_name=_("Faktisk forbrug")
    )
    bartendersInCharge = models.ManyToManyField(
        Bartender, blank=True, verbose_name=_("Ansvarlige")
    )
    billSendTo = models.CharField(max_length=140, verbose_name=_("Send regning til"))
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="notsent")
    invoice_number = models.CharField(
        max_length=32, blank=True, verbose_name=_("Fakturanummer")
    )
    total_price = models.DecimalField(
        max_digits=9 + 2,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Total pris"),
    )
    payment_due_date = models.DateField(
        blank=True, null=True, verbose_name=_("Betalingsdato")
    )

    class Meta:
        ordering = ("dateFrom",)


class UdlejningApplication(UdlejningCommon):
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created",)

    def accept(self):
        common_fields = super()._meta.get_fields()
        value_dict = {f.name: getattr(self, f.name) for f in common_fields}
        u = Udlejning.objects.create(**value_dict)
        return u.pk


class UdlejningGrill(models.Model):
    dateFrom = models.DateTimeField()
    dateTo = models.DateTimeField(blank=True, null=True)
    whoReserved = models.TextField(max_length=140)
    where = models.TextField(max_length=140)
    contactInfo = models.CharField(max_length=140)
    comments = models.TextField(blank=True)
    bartendersInCharge = models.ManyToManyField(Bartender, blank=True)

    class Meta:
        ordering = ("dateFrom",)


class UdlejningProjector(models.Model):
    dateFrom = models.DateTimeField()
    dateTo = models.DateTimeField()
    whoReserved = models.TextField(max_length=140, blank=True)
    contactInfo = models.CharField(max_length=140, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ("dateFrom",)


class UdlejningSpeakers(models.Model):
    dateFrom = models.DateTimeField()
    dateTo = models.DateTimeField()
    whoReserved = models.TextField(max_length=140, blank=True)
    contactInfo = models.CharField(max_length=140, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ("dateFrom",)
