from django.db import models


class Player(models.Model):
    id = models.IntegerField(primary_key=True, unique=True, blank=False, editable=False, auto_created=False)
    player_name = models.CharField(max_length=50)
    entry_name = models.CharField(max_length=50)
    displayed_name = models.CharField(max_length=50) 


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

    player = models.ForeignKey(Player, verbose_name='Player', on_delete=models.PROTECT)
    paid = models.BooleanField()
    method = models.CharField(max_length=6, choices=PAYMENT_METHODS)
    amount = models.IntegerField(default=FANTASY_COST)


class WinTotals(models.Model):
    player = models.ForeignKey(Player, verbose_name='Player', on_delete=models.PROTECT)
    weekly_wins = models.IntegerField()
    winnings = models.IntegerField()
    season_winner = models.BooleanField()
    total_winnings = models.IntegerField()


class Points(models.Model):
    week = models.IntegerField()
    player = models.ForeignKey(Player, verbose_name='Player', on_delete=models.PROTECT)
    total_points = models.IntegerField(default=0)
    transfer_cost = models.IntegerField(default=0)
    max_points = models.BooleanField()