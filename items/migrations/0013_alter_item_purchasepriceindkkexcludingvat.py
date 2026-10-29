from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("items", "0012_rename_purchasepriceindkk_purchasepriceindkkexcludingvat"),
    ]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="purchasePriceInDKKExcludingVAT",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=11,
                null=True,
                verbose_name="Purchase price (DKK) excluding VAT",
            ),
        ),
    ]
