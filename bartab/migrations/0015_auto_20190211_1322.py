# Generated by Django 2.1.5 on 2019-02-11 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bartab', '0014_auto_20190211_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printer',
            name='name',
            field=models.CharField(max_length=32, unique=True),
        ),
    ]