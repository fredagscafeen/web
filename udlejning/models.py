from django.db import models

from bartenders.models import Bartender


class UdlejningCommon(models.Model):
    class Meta:
        abstract = True

    PAYMENT_CHOICES = (
        ("EAN", "EAN"),
        ("invoice", "Faktura"),
        ("card", "Kort i baren"),
    )

    dateFrom = models.DateTimeField(
        verbose_name="Start dato & tid",
        help_text="Hvornår skal anlægget afhentes/stilles op?",
    )
    dateTo = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Slut dato & tid",
        help_text="Hvornår skal anlægget afleveres/pilles ned?",
    )
    whoReserved = models.CharField(max_length=140, verbose_name="Hvem er I?")

    contactEmail = models.EmailField(verbose_name="Email til kontaktperson")
    contactPhone = models.IntegerField(
        verbose_name="Telefonnummer til kontaktperson", blank=True, null=True
    )

    whoPays = models.CharField(
        max_length=140,
        verbose_name="Hvem betaler?",
        help_text="Hvem skal regningen sendes til? (Fulde navn på person, virksomhed eller organisation)",
    )
    paymentType = models.CharField(
        max_length=140,
        choices=PAYMENT_CHOICES,
        verbose_name="Betalingsform",
        help_text="Hvordan bliver der betalt?",
    )

    EANnumber = models.BigIntegerField(
        verbose_name="EAN-nummer",
        blank=True,
        null=True,
        help_text="Skal kun angives, hvis der skal faktureres til et EAN-nummer",
    )

    where = models.TextField(
        max_length=140,
        verbose_name="Lokation",
        help_text="Hvor bliver arrangmentet afholdt?",
    )
    expectedConsummation = models.TextField(
        max_length=140,
        verbose_name="Forventet forbrug",
        help_text="Hvilke slags øl eller andre drikkevarer ønskes der og hvor mange fustager af hver type?",
    )
    comments = models.TextField(blank=True, verbose_name="Kommentarer")

    def __str__(self):
        return f"{self.dateFrom} {self.whoReserved}"


class UdlejningForegoing(UdlejningCommon):
    ASSOCIATION_CHOICES = (
        ("internal", "Intern"),
        ("external", "Ekstern"),
    )

    STATUS_CHOICES = (
        ("notsent", "Regning ikke sendt"),
        ("sent", "Regning sendt"),
        ("paid", "Regning betalt"),
    )

    SYSTEM_CHOICES = (
        ("small", "Lille"),
        ("medium", "Mellem"),
    )

    draftBeerSystem = models.CharField(
        max_length=16,
        choices=SYSTEM_CHOICES,
        blank=True,
        verbose_name="Fadølsanlæg",
        help_text="Hvilket anlæg vil I låne?",
    )
    association = models.CharField(
        max_length=16,
        choices=ASSOCIATION_CHOICES,
        blank=True,
        verbose_name="Tilknytning",
    )
    actualConsummation = models.TextField(
        max_length=140, blank=True, verbose_name="Faktisk forbrug"
    )
    bartendersInCharge = models.ManyToManyField(
        Bartender, blank=True, verbose_name="Ansvarlige"
    )
    billSendTo = models.CharField(max_length=140, verbose_name="Send regning til")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="notsent")
    invoice_number = models.CharField(
        max_length=32, blank=True, verbose_name="Fakturanummer"
    )
    total_price = models.DecimalField(
        max_digits=9 + 2,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Total pris",
    )
    payment_due_date = models.DateField(
        blank=True, null=True, verbose_name="Betalingsdato"
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
        u = UdlejningForegoing.objects.create(**value_dict)
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


class UdlejningSpeaker(models.Model):
    dateFrom = models.DateTimeField()
    dateTo = models.DateTimeField()
    whoReserved = models.TextField(max_length=140, blank=True)
    contactInfo = models.CharField(max_length=140, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ("dateFrom",)
