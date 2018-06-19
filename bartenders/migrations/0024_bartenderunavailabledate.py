# Generated by Django 2.0.6 on 2018-06-19 21:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('bartenders', '0023_bartender_email_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='BartenderUnavailableDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('bartender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unavailable_dates', to='bartenders.Bartender')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='bartenderunavailabledate',
            unique_together={('bartender', 'date')},
        ),
    ]
