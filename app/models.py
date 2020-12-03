from django.db import models

from typing import List

class Player(models.Model):
    id = models.IntegerField(primary_key=True, unique=True, blank=False, editable=False, auto_created=False)
    player_name = models.CharField(max_length=50)
    entry_name = models.CharField(max_length=50)
    displayed_name = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.player_name} | {self.entry_name} | {self.displayed_name}'
    
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
            row = [week_total for week_total in self.filter(week=week).order_by('player')]
            results.append(row)
        return results

    def total_points_diff(self) -> List:        
        latest_week = self.last().week
        current_total_leader = self.filter(week=latest_week, current_leader=True)
        if current_total_leader:
            current_total_leader_points = current_total_leader[0]
            return [current_total_leader_points.total_points - week_points.total_points for week_points in self.filter(week=latest_week).order_by('player')]
        return [0] * self.filter(week=latest_week).count()


class Points(models.Model):
    week = models.IntegerField()
    player = models.ForeignKey(Player, verbose_name='Player', on_delete=models.PROTECT)
    total_points = models.IntegerField(default=0)
    transfer_cost = models.IntegerField(default=0)
    final_points = models.BooleanField()
    net_weekly_points = models.IntegerField(default=0)
    max_points = models.BooleanField()  # should be renamed to weekly_winner
    current_leader = models.BooleanField()

    objects = PointsQuerySet.as_manager()

    def __str__(self):
        return f'{self.player.displayed_name} | Week: {self.week} | {self.net_weekly_points}'
    
    class Meta:
       ordering = ['week', 'player']

    @property
    def weekly_winner(self):
        return ','.join([winner.player.displayed_name for winner in Points.objects.filter(week=self.week, max_points=True).order_by('player')])