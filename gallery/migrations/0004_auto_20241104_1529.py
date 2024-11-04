# Generated by Django 3.2.4 on 2024-11-04 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gallery", "0003_album_thumbnail"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="basemedia",
            name="isCoverFile",
        ),
        migrations.AlterField(
            model_name="album",
            name="thumbnail",
            field=models.ImageField(
                blank=True, null=True, upload_to="galleries", verbose_name="Thumbnail"
            ),
        ),
    ]
