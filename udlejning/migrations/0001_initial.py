# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-08 09:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Udlejning',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dateFrom', models.DateTimeField()),
                ('dateTo', models.DateTimeField(blank=True, null=True)),
                ('whoReserved', models.TextField(max_length=140)),
                ('whoPays', models.TextField(max_length=140)),
                ('paymentType', models.CharField(max_length=140)),
                ('billSendTo', models.CharField(max_length=140)),
                ('where', models.TextField(max_length=140)),
                ('expectedConsummation', models.TextField(max_length=140)),
                ('actualConsummation', models.TextField(max_length=140, blank=True, null=True)),
                ('contactInfo', models.CharField(max_length=140)),
                ('comments', models.TextField(blank=True, null=True)),
                ('boardMemberInCharge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bartenders.BoardMember')),
                ('paid', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='UdlejningGrill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dateFrom', models.DateTimeField()),
                ('dateTo', models.DateTimeField(blank=True, null=True)),
                ('whoReserved', models.TextField(max_length=140)),
                ('where', models.TextField(max_length=140)),
                ('contactInfo', models.CharField(max_length=140)),
                ('comments', models.TextField(blank=True, null=True)),
                ('boardMemberInCharge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bartenders.BoardMember')),
            ],
        ),
    ]

