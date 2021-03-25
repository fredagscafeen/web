# Generated by Django 3.1.2 on 2021-02-03 15:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bartenders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Poll",
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
                ("name", models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="BallotLink",
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
                ("url", models.URLField()),
                (
                    "bartender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bartenders.bartender",
                    ),
                ),
                (
                    "poll",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bartenders.poll",
                    ),
                ),
            ],
        ),
    ]