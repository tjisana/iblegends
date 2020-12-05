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
        self.stdout.write(self.style.SUCCESS('Weekly winnings updated'))