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

    player = models.ForeignKey(Player, verbose_name='Player', on_delete=models.SET_DEFAULT)
    paid = models.BooleanField()
    method = models.CharField(choices=PAYMENT_METHODS)
    amount = models.IntegerField(max_length=3, default=FANTASY_COST)


class WinTotals(models.Model):
    player = models.ForeignKey(Player, verbose_name='Player', on_delete=models.SET_DEFAULT)
    weekly_wins = models.IntegerField(max_length=2)
    winnings = models.IntegerField(max_length=3)
    season_winner = models.BooleanField()
    total_winnings = models.IntegerField(max_length=4)


class Points(models.Model):
    week = models.IntegerField(max_length=2)
    player = models.ForeignKey(Player, verbose_name='Player', on_delete=models.SET_DEFAULT)
    max_points = models.BooleanField()