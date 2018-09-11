# Generated by Django 2.0.8 on 2018-09-11 09:11

import bartab.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bartab', '0010_auto_20180911_1105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bartabentry',
            name='raw_added',
            field=bartab.models.SumField(blank=True, verbose_name='Indsat'),
        ),
        migrations.AlterField(
            model_name='bartabentry',
            name='raw_used',
            field=bartab.models.SumField(blank=True, verbose_name='Køb'),
        ),
        migrations.AlterField(
            model_name='bartabentry',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='bartab.BarTabUser', verbose_name='Bruger'),
        ),
    ]