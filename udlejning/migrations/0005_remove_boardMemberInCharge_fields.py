# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-03-25 16:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("udlejning", "0004_copy_boardMember_bartender_fk"),
    ]

    operations = [
        migrations.RemoveField(model_name="udlejning", name="boardMemberInCharge",),
        migrations.RemoveField(
            model_name="udlejninggrill", name="boardMemberInCharge",
        ),
    ]
