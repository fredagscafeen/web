from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def delete_existing_expenses(apps, schema_editor):
    OutOfPocketExpense = apps.get_model("accountant", "OutOfPocketExpense")
    OutOfPocketExpense.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accountant", "0002_outofpocketexpenseitem_date"),
    ]

    operations = [
        migrations.RunPython(delete_existing_expenses, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="outofpocketexpense",
            name="bartender",
        ),
        migrations.AddField(
            model_name="outofpocketexpense",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="out_of_pocket_expenses",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
                help_text="The user this expense belongs to. Can edit it until it is completed.",
            ),
        ),
    ]
