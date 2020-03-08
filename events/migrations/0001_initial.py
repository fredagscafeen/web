# Generated by Django 2.2.2 on 2019-06-10 22:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("bartenders", "0035_auto_20190521_0436"),
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
                ("description", models.TextField(blank=True)),
                ("start_datetime", models.DateTimeField()),
                ("end_datetime", models.DateTimeField()),
                ("response_deadline", models.DateTimeField()),
            ],
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
                (
                    "event_choice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="options",
                        to="events.EventChoice",
                    ),
                ),
            ],
            options={"unique_together": {("event_choice", "option")},},
        ),
        migrations.CreateModel(
            name="EventChoiceResponse",
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
                    "option",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="events.EventChoiceOption",
                    ),
                ),
            ],
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
                    "respo",
                    models.ManyToManyField(
                        through="events.EventChoiceResponse",
                        to="events.EventChoiceOption",
                    ),
                ),
            ],
            options={"unique_together": {("event", "bartender")},},
        ),
        migrations.AddField(
            model_name="eventchoiceresponse",
            name="response",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="events.EventResponse"
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="event_choices",
            field=models.ManyToManyField(to="events.EventChoice"),
        ),
    ]
