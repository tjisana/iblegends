from django.db import models

from typing import List

class Player(models.Model):
    id = models.IntegerField(primary_key=True, unique=True, blank=False, editable=False, auto_created=False)
    player_name = models.CharField(max_length=50)
    entry_name = models.CharField(max_length=50)
    displayed_name = models.CharField(max_length=50)

    class Meta:
       ordering = ['displayed_name']


class Payment(models.Model):

    UNPAID = None
    CASH = 1
    VENMO = 2

    PAYMENT_METHODS = (
        (UNPAID, 'Unpaid'),
        (CASH, 'Cash'),
        (VENMO, 'Venmo')
    )

    FANTASY_COST = 200

    player = models.OneToOneField(Player, verbose_name='Player', primary_key=True, on_delete=models.PROTECT)
    paid = models.BooleanField()
    method = models.CharField(max_length=6, choices=PAYMENT_METHODS)
    amount = models.IntegerField(default=FANTASY_COST)


class WinTotals(models.Model):

    WEEKLY_PRIZE = 25

    player = models.OneToOneField(Player, verbose_name='Player', primary_key=True, on_delete=models.PROTECT)
    weekly_wins = models.IntegerField()
    winnings = models.IntegerField()
    season_winner = models.BooleanField()
    total_winnings = models.IntegerField()


class PointsQuerySet(models.QuerySet):
    def weekly_results(self) -> List:
        latest_week = self.last().week
        results = []
        for week in range(1, latest_week + 1):
            row = [week_total.net_weekly_points for week_total in self.filter(week=week).order_by('player')]
            weekly_winner = ','.join([winner.player.displayed_name for winner in self.filter(week=week, max_points=True).order_by('player')])
            results.append([week, *row, weekly_winner])            
        return results


class Points(models.Model):
    week = models.IntegerField()
    player = models.ForeignKey(Player, verbose_name='Player', on_delete=models.PROTECT)
    total_points = models.IntegerField(default=0)
    transfer_cost = models.IntegerField(default=0)
    final_points = models.BooleanField()
    net_weekly_points = models.IntegerField(default=0)
    max_points = models.BooleanField()

    objects = PointsQuerySet.as_manager()

    class Meta:
       ordering = ['week', 'player']