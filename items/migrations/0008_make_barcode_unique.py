from django.db import migrations, models


def set_barcode_nulls(apps, schema_editor):
    Item = apps.get_model('items', 'Item')
    for item in Item.objects.all():
        if not item.barcode:
            item.barcode = None
            item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0007_auto_20190324_2239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='barcode',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RunPython(set_barcode_nulls),
        migrations.AlterField(
            model_name='item',
            name='barcode',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
