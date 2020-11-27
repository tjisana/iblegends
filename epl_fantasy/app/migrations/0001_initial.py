# Generated by Django 3.1.3 on 2020-11-27 01:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.IntegerField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('player_name', models.CharField(max_length=50)),
                ('entry_name', models.CharField(max_length=50)),
                ('displayed_name', models.CharField(max_length=50)),
            ],
            options={
                'ordering': ['displayed_name'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, serialize=False, to='app.player', verbose_name='Player')),
                ('paid', models.BooleanField()),
                ('method', models.CharField(choices=[(None, 'Unpaid'), (1, 'Cash'), (2, 'Venmo')], max_length=6)),
                ('amount', models.IntegerField(default=200)),
            ],
        ),
        migrations.CreateModel(
            name='WinTotals',
            fields=[
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, serialize=False, to='app.player', verbose_name='Player')),
                ('weekly_wins', models.IntegerField()),
                ('winnings', models.IntegerField()),
                ('season_winner', models.BooleanField()),
                ('total_winnings', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Points',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week', models.IntegerField()),
                ('total_points', models.IntegerField(default=0)),
                ('transfer_cost', models.IntegerField(default=0)),
                ('final_points', models.BooleanField()),
                ('net_weekly_points', models.IntegerField(default=0)),
                ('max_points', models.BooleanField()),
                ('current_leader', models.BooleanField()),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app.player', verbose_name='Player')),
            ],
            options={
                'ordering': ['week', 'player'],
            },
        ),
    ]
