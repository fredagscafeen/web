# Generated by Django 2.0.8 on 2018-09-11 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bartab", "0008_auto_20180709_0029"),
    ]

    operations = [
        migrations.AddField(
            model_name="bartabentry",
            name="added_cash",
            field=models.NullBooleanField(),
        ),
    ]
