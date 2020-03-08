# Generated by Django 2.0.3 on 2018-03-14 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("items", "0004_auto_20180314_0323"),
    ]

    operations = [
        migrations.AlterField(
            model_name="beertype",
            name="description",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="beertype",
            name="link",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="brewery",
            name="description",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="brewery",
            name="website",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="item",
            name="barcode",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="item",
            name="container",
            field=models.CharField(
                blank=True,
                choices=[
                    ("DRAFT", "Fad"),
                    ("BOTTLE", "Flaske"),
                    ("SHOT", "Shot"),
                    ("FOOD", "Madvare"),
                    ("OTHER", "Andet"),
                ],
                default="",
                max_length=140,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="item",
            name="country",
            field=models.CharField(blank=True, default="", max_length=140),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="item",
            name="description",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="item",
            name="imageUrl",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="item",
            name="link",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
    ]
