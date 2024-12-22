# Generated by Django 3.2.4 on 2024-12-12 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "bartenders",
            "0004_alter_bartender_email_alter_bartender_tshirt_size_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="bartendershift",
            options={"ordering": ("-start_datetime",)},
        ),
        migrations.AlterField(
            model_name="bartender",
            name="email",
            field=models.EmailField(
                help_text="En post.au mail fungerer ikke",
                max_length=254,
                unique=True,
                verbose_name="E-mail",
            ),
        ),
        migrations.AlterField(
            model_name="bartender",
            name="studentNumber",
            field=models.IntegerField(null=True, verbose_name="Studienummer"),
        ),
        migrations.AlterField(
            model_name="bartenderapplication",
            name="email",
            field=models.EmailField(
                help_text="En post.au mail fungerer ikke",
                max_length=254,
                unique=True,
                verbose_name="E-mail",
            ),
        ),
        migrations.AlterField(
            model_name="bartenderapplication",
            name="info",
            field=models.TextField(
                help_text="Fortæl lidt om dig selv, og hvorfor du tror at lige præcist du, ville være en god bartender"
            ),
        ),
        migrations.AlterField(
            model_name="bartenderapplication",
            name="studentNumber",
            field=models.IntegerField(null=True, verbose_name="Studienummer"),
        ),
    ]