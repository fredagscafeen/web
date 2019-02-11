# Generated by Django 2.1.5 on 2019-02-11 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('bartab', '0012_printer'), ('bartab', '0013_auto_20190211_1111'), ('bartab', '0014_auto_20190211_1112')]

    dependencies = [
        ('bartab', '0011_auto_20180911_1111'),
    ]

    operations = [
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('nygaard-394', 'nygaard-394'), ('studiecafeen', 'studiecafeen')], max_length=32, unique=True)),
            ],
        ),
    ]
