# Generated by Django 3.1.3 on 2020-12-04 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wintotals',
            name='total_winnings',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
        migrations.AlterField(
            model_name='wintotals',
            name='winnings',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
    ]