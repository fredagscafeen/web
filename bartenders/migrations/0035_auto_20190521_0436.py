# Generated by Django 2.2 on 2019-05-21 02:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bartenders", "0034_auto_20190520_2331"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bartendershift",
            name="period",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="shifts",
                to="bartenders.BartenderShiftPeriod",
            ),
        ),
    ]
