from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("items", "0011_alter_item_brewery_alter_item_type"),
    ]

    operations = [
        migrations.RenameField(
            model_name="item",
            old_name="purchasePriceInDKK",
            new_name="purchasePriceInDKKExcludingVAT",
        ),
    ]
