from django.core.management.base import BaseCommand, CommandError

from app.models import Points, WinTotals
from app.utils import update_weekly_winner

import json
import os
import requests


class Command(BaseCommand):
    help = 'Populates WinTotals Table'
    
    def handle(self, *args, **options):
        #  first update Points table
        last_finalized_week = Points.objects.last().week        
        for week_number in range(1, last_finalized_week+1):
            update_weekly_winner(week_number)
        self.stdout.write(self.style.SUCCESS('Max points columns updated in Points table'))
        for weekly_winner in Points.objects.filter(max_points=True):
            winner = WinTotals.objects.get(player=weekly_winner.player)
            winner.weekly_wins += 1
            winner.winnings += WinTotals.WEEKLY_PRIZE
            winner.total_winnings += WinTotals.WEEKLY_PRIZE
            winner.save()
