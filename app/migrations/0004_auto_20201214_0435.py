# Generated by Django 3.1.3 on 2020-12-14 04:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20201204_2333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='player',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='payment', serialize=False, to='app.player', verbose_name='Player'),
        ),
        migrations.AlterField(
            model_name='points',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='point', to='app.player', verbose_name='Player'),
        ),
        migrations.AlterField(
            model_name='wintotals',
            name='player',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='wintotal', serialize=False, to='app.player', verbose_name='Player'),
        ),
    ]