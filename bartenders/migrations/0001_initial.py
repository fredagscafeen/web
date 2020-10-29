# Generated by Django 3.0.6 on 2020-10-06 13:45

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import bartenders.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Bartender",
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
                ("name", models.CharField(max_length=140, verbose_name="Fulde navn")),
                (
                    "username",
                    models.CharField(
                        max_length=140, unique=True, verbose_name="Brugernavn"
                    ),
                ),
                ("email", models.CharField(blank=True, max_length=255, unique=True)),
                (
                    "studentNumber",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Studienummer"
                    ),
                ),
                (
                    "phoneNumber",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Telefonnummer"
                    ),
                ),
                (
                    "tshirt_size",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("XS", "XS"),
                            ("S", "S"),
                            ("M", "M"),
                            ("L", "L"),
                            ("XL", "XL"),
                            ("XXL", "XXL"),
                            ("XXXL", "XXXL"),
                        ],
                        max_length=10,
                        null=True,
                        verbose_name="T-shirt størrelse",
                    ),
                ),
                ("isActiveBartender", models.BooleanField(default=True)),
                (
                    "prefer_only_early_shifts",
                    models.BooleanField(
                        default=False,
                        verbose_name="Jeg foretrækker ikke at have nogle sene barvagter",
                    ),
                ),
            ],
            options={
                "ordering": ("-isActiveBartender", "name"),
            },
        ),
        migrations.CreateModel(
            name="BartenderApplication",
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
                ("name", models.CharField(max_length=140, verbose_name="Fulde navn")),
                (
                    "username",
                    models.CharField(
                        max_length=140, unique=True, verbose_name="Brugernavn"
                    ),
                ),
                ("email", models.CharField(blank=True, max_length=255, unique=True)),
                (
                    "studentNumber",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Studienummer"
                    ),
                ),
                (
                    "phoneNumber",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Telefonnummer"
                    ),
                ),
                (
                    "tshirt_size",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("XS", "XS"),
                            ("S", "S"),
                            ("M", "M"),
                            ("L", "L"),
                            ("XL", "XL"),
                            ("XXL", "XXL"),
                            ("XXXL", "XXXL"),
                        ],
                        max_length=10,
                        null=True,
                        verbose_name="T-shirt størrelse",
                    ),
                ),
                ("study", models.CharField(max_length=50, verbose_name="Studie")),
                ("study_year", models.IntegerField(verbose_name="Årgang")),
                (
                    "info",
                    models.TextField(
                        blank=True,
                        help_text="Eventuelle ekstra info til bestyrelsen skrives her",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("created",),
            },
        ),
        migrations.CreateModel(
            name="BartenderShiftPeriod",
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
                    "generation_datetime",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
            ],
            options={
                "ordering": ("-generation_datetime",),
            },
        ),
        migrations.CreateModel(
            name="BoardMemberDepositShiftPeriod",
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
                    "generation_datetime",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BoardMemberPeriod",
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
                ("start_date", models.DateField(unique=True)),
            ],
            options={
                "ordering": ("-start_date",),
            },
        ),
        migrations.CreateModel(
            name="BoardMemberDepositShift",
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
                    "start_date",
                    models.DateField(
                        default=bartenders.models.next_deposit_shift_start
                    ),
                ),
                ("end_date", models.DateField(blank=True)),
                (
                    "period",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="bartenders.BoardMemberDepositShiftPeriod",
                    ),
                ),
                (
                    "responsibles",
                    models.ManyToManyField(
                        related_name="deposit_shifts", to="bartenders.Bartender"
                    ),
                ),
            ],
            options={
                "ordering": ("start_date",),
            },
        ),
        migrations.CreateModel(
            name="BartenderShift",
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
                    "start_datetime",
                    models.DateTimeField(
                        default=bartenders.models.next_bartender_shift_start
                    ),
                ),
                ("end_datetime", models.DateTimeField(blank=True)),
                (
                    "other_bartenders",
                    models.ManyToManyField(
                        blank=True, related_name="shifts", to="bartenders.Bartender"
                    ),
                ),
                (
                    "period",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="shifts",
                        to="bartenders.BartenderShiftPeriod",
                    ),
                ),
                (
                    "responsible",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="bartenders.Bartender",
                    ),
                ),
            ],
            options={
                "ordering": ("start_datetime",),
            },
        ),
        migrations.CreateModel(
            name="BoardMember",
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
                ("title", models.CharField(max_length=255)),
                ("responsibilities", models.CharField(max_length=255)),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="boardMembers"),
                ),
                (
                    "bartender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="board_members",
                        to="bartenders.Bartender",
                    ),
                ),
                (
                    "period",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bartenders.BoardMemberPeriod",
                    ),
                ),
            ],
            options={
                "ordering": ("period", "title"),
                "unique_together": {("bartender", "period")},
            },
        ),
        migrations.CreateModel(
            name="BartenderUnavailableDate",
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
                ("date", models.DateField()),
                (
                    "bartender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unavailable_dates",
                        to="bartenders.Bartender",
                    ),
                ),
            ],
            options={
                "unique_together": {("bartender", "date")},
            },
        ),
    ]
