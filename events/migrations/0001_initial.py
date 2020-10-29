# Generated by Django 3.0.6 on 2020-10-06 13:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("bartenders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
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
                ("name", models.CharField(max_length=255)),
                ("location", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("start_datetime", models.DateTimeField()),
                ("end_datetime", models.DateTimeField()),
                ("response_deadline", models.DateTimeField()),
                (
                    "bartender_blacklist",
                    models.ManyToManyField(
                        blank=True,
                        related_name="blacklisted_events",
                        to="bartenders.Bartender",
                    ),
                ),
                (
                    "bartender_whitelist",
                    models.ManyToManyField(
                        blank=True,
                        related_name="whitelisted_events",
                        to="bartenders.Bartender",
                    ),
                ),
            ],
            options={
                "ordering": ("-start_datetime",),
            },
        ),
        migrations.CreateModel(
            name="EventChoice",
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
                ("name", models.CharField(max_length=255)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_choices",
                        to="events.Event",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EventChoiceOption",
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
                ("option", models.CharField(max_length=255)),
                ("max_selected", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "event_choice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="options",
                        to="events.EventChoice",
                    ),
                ),
            ],
            options={
                "unique_together": {("event_choice", "option")},
            },
        ),
        migrations.CreateModel(
            name="EventResponse",
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
                ("attending", models.BooleanField()),
                (
                    "bartender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bartenders.Bartender",
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="events.Event",
                    ),
                ),
                (
                    "selected_options",
                    models.ManyToManyField(to="events.EventChoiceOption"),
                ),
            ],
            options={
                "unique_together": {("event", "bartender")},
            },
        ),
    ]
