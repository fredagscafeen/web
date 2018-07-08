# Generated by Django 2.0.6 on 2018-07-08 21:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bartab', '0003_auto_20180618_0150'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bartabentry',
            options={'ordering': ('snapshot__last_updated',)},
        ),
        migrations.AlterModelOptions(
            name='bartabsnapshot',
            options={'ordering': ('-last_updated',)},
        ),
        migrations.RenameField(
            model_name='bartabsnapshot',
            old_name='timestamp',
            new_name='last_updated',
        ),
    ]