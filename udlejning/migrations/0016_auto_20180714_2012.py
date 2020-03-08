# Generated by Django 2.0.7 on 2018-07-14 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("udlejning", "0015_auto_20180713_1758"),
    ]

    operations = [
        migrations.AlterField(
            model_name="udlejning",
            name="paymentType",
            field=models.CharField(
                choices=[
                    ("EAN", "EAN"),
                    ("invoice", "Faktura"),
                    ("card", "Kort i baren"),
                ],
                help_text='Hvordan bliver der betalt? Vi tilbyder også at fakturere til EAN-nummer (e-faktura) mod gebyr. <a class="external text" href="mailto:best@fredagscafeen.dk">Kontakt os</a> for at høre nærmere.',
                max_length=140,
                verbose_name="Betalingsform",
            ),
        ),
        migrations.AlterField(
            model_name="udlejningapplication",
            name="paymentType",
            field=models.CharField(
                choices=[
                    ("EAN", "EAN"),
                    ("invoice", "Faktura"),
                    ("card", "Kort i baren"),
                ],
                help_text='Hvordan bliver der betalt? Vi tilbyder også at fakturere til EAN-nummer (e-faktura) mod gebyr. <a class="external text" href="mailto:best@fredagscafeen.dk">Kontakt os</a> for at høre nærmere.',
                max_length=140,
                verbose_name="Betalingsform",
            ),
        ),
    ]
