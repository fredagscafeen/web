# Generated by Django 3.0.6 on 2020-10-06 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("bartenders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UdlejningApplication",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "dateFrom",
                    models.DateTimeField(
                        help_text="Hvornår skal anlægget afhentes/stilles op?",
                        verbose_name="Start dato & tid",
                    ),
                ),
                (
                    "dateTo",
                    models.DateTimeField(
                        blank=True,
                        help_text="Hvornår skal anlægget afleveres/pilles ned?",
                        null=True,
                        verbose_name="Slut dato & tid",
                    ),
                ),
                (
                    "whoReserved",
                    models.CharField(max_length=140, verbose_name="Hvem er I?"),
                ),
                (
                    "contactEmail",
                    models.EmailField(
                        max_length=254, verbose_name="Email til kontaktperson"
                    ),
                ),
                (
                    "contactPhone",
                    models.IntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Telefonnummer til kontaktperson",
                    ),
                ),
                (
                    "whoPays",
                    models.CharField(
                        help_text="Hvem skal regningen sendes til? (Fulde navn på person, virksomhed eller organisation)",
                        max_length=140,
                        verbose_name="Hvem betaler?",
                    ),
                ),
                (
                    "paymentType",
                    models.CharField(
                        choices=[
                            ("EAN", "EAN"),
                            ("invoice", "Faktura"),
                            ("card", "Kort i baren"),
                        ],
                        help_text="Hvordan bliver der betalt?",
                        max_length=140,
                        verbose_name="Betalingsform",
                    ),
                ),
                (
                    "EANnumber",
                    models.BigIntegerField(
                        blank=True,
                        help_text="Skal kun angives, hvis der skal faktureres til et EAN-nummer",
                        null=True,
                        verbose_name="EAN-nummer",
                    ),
                ),
                (
                    "where",
                    models.TextField(
                        help_text="Hvor bliver arrangmentet afholdt?",
                        max_length=140,
                        verbose_name="Lokation",
                    ),
                ),
                (
                    "expectedConsummation",
                    models.TextField(
                        help_text="Hvilke slags øl eller andre drikkevarer ønskes der og hvor mange fustager af hver type?",
                        max_length=140,
                        verbose_name="Forventet forbrug",
                    ),
                ),
                ("comments", models.TextField(blank=True, verbose_name="Kommentarer")),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("created",),
            },
        ),
        migrations.CreateModel(
            name="UdlejningProjector",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("dateFrom", models.DateTimeField()),
                ("dateTo", models.DateTimeField()),
                ("whoReserved", models.TextField(blank=True, max_length=140)),
                ("contactInfo", models.CharField(blank=True, max_length=140)),
                ("comments", models.TextField(blank=True)),
            ],
            options={
                "ordering": ("dateFrom",),
            },
        ),
        migrations.CreateModel(
            name="UdlejningSpeakers",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("dateFrom", models.DateTimeField()),
                ("dateTo", models.DateTimeField()),
                ("whoReserved", models.TextField(blank=True, max_length=140)),
                ("contactInfo", models.CharField(blank=True, max_length=140)),
                ("comments", models.TextField(blank=True)),
            ],
            options={
                "ordering": ("dateFrom",),
            },
        ),
        migrations.CreateModel(
            name="UdlejningGrill",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("dateFrom", models.DateTimeField()),
                ("dateTo", models.DateTimeField(blank=True, null=True)),
                ("whoReserved", models.TextField(max_length=140)),
                ("where", models.TextField(max_length=140)),
                ("contactInfo", models.CharField(max_length=140)),
                ("comments", models.TextField(blank=True)),
                (
                    "bartendersInCharge",
                    models.ManyToManyField(blank=True, to="bartenders.Bartender"),
                ),
            ],
            options={
                "ordering": ("dateFrom",),
            },
        ),
        migrations.CreateModel(
            name="UdlejningForegoing",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "dateFrom",
                    models.DateTimeField(
                        help_text="Hvornår skal anlægget afhentes/stilles op?",
                        verbose_name="Start dato & tid",
                    ),
                ),
                (
                    "dateTo",
                    models.DateTimeField(
                        blank=True,
                        help_text="Hvornår skal anlægget afleveres/pilles ned?",
                        null=True,
                        verbose_name="Slut dato & tid",
                    ),
                ),
                (
                    "whoReserved",
                    models.CharField(max_length=140, verbose_name="Hvem er I?"),
                ),
                (
                    "contactEmail",
                    models.EmailField(
                        max_length=254, verbose_name="Email til kontaktperson"
                    ),
                ),
                (
                    "contactPhone",
                    models.IntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Telefonnummer til kontaktperson",
                    ),
                ),
                (
                    "whoPays",
                    models.CharField(
                        help_text="Hvem skal regningen sendes til? (Fulde navn på person, virksomhed eller organisation)",
                        max_length=140,
                        verbose_name="Hvem betaler?",
                    ),
                ),
                (
                    "paymentType",
                    models.CharField(
                        choices=[
                            ("EAN", "EAN"),
                            ("invoice", "Faktura"),
                            ("card", "Kort i baren"),
                        ],
                        help_text="Hvordan bliver der betalt?",
                        max_length=140,
                        verbose_name="Betalingsform",
                    ),
                ),
                (
                    "EANnumber",
                    models.BigIntegerField(
                        blank=True,
                        help_text="Skal kun angives, hvis der skal faktureres til et EAN-nummer",
                        null=True,
                        verbose_name="EAN-nummer",
                    ),
                ),
                (
                    "where",
                    models.TextField(
                        help_text="Hvor bliver arrangmentet afholdt?",
                        max_length=140,
                        verbose_name="Lokation",
                    ),
                ),
                (
                    "expectedConsummation",
                    models.TextField(
                        help_text="Hvilke slags øl eller andre drikkevarer ønskes der og hvor mange fustager af hver type?",
                        max_length=140,
                        verbose_name="Forventet forbrug",
                    ),
                ),
                ("comments", models.TextField(blank=True, verbose_name="Kommentarer")),
                (
                    "draftBeerSystem",
                    models.CharField(
                        blank=True,
                        choices=[("small", "Lille"), ("medium", "Mellem")],
                        help_text="Hvilket anlæg vil I låne?",
                        max_length=16,
                        verbose_name="Fadølsanlæg",
                    ),
                ),
                (
                    "association",
                    models.CharField(
                        blank=True,
                        choices=[("internal", "Intern"), ("external", "Ekstern")],
                        max_length=16,
                        verbose_name="Tilknytning",
                    ),
                ),
                (
                    "actualConsummation",
                    models.TextField(
                        blank=True, max_length=140, verbose_name="Faktisk forbrug"
                    ),
                ),
                (
                    "billSendTo",
                    models.CharField(max_length=140, verbose_name="Send regning til"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("notsent", "Regning ikke sendt"),
                            ("sent", "Regning sendt"),
                            ("paid", "Regning betalt"),
                        ],
                        default="notsent",
                        max_length=16,
                    ),
                ),
                (
                    "invoice_number",
                    models.CharField(
                        blank=True, max_length=32, verbose_name="Fakturanummer"
                    ),
                ),
                (
                    "total_price",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=11,
                        null=True,
                        verbose_name="Total pris",
                    ),
                ),
                (
                    "payment_due_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Betalingsdato"
                    ),
                ),
                (
                    "bartendersInCharge",
                    models.ManyToManyField(
                        blank=True, to="bartenders.Bartender", verbose_name="Ansvarlige"
                    ),
                ),
            ],
            options={
                "ordering": ("dateFrom",),
            },
        ),
    ]
