# Generated by Django 2.1.5 on 2019-01-28 23:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bartenders", "0030_boardmemberperiod"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="boardmemberperiod", options={"ordering": ("-start_date",)},
        ),
    ]
