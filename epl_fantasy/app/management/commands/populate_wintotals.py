from django.core.management.base import BaseCommand, CommandError

from app.models import Points

import json
import os
import requests


class Command(BaseCommand):
    help = 'Populates WinTotals Table'
    
    def handle(self, *args, **options):
        #  first update Points table
        last_finalized_week = Points.objects.last().week        
        for week_number in range(1, last_finalized_week+1):
            max_net_weekly_points = -1000
            for player_weekly_score in Points.objects.filter(week=week_number).order_by('-net_weekly_points'):
                if player_weekly_score.net_weekly_points >= max_net_weekly_points:
                    player_weekly_score.max_points = True
                    player_weekly_score.save()
                    max_net_weekly_points = player_weekly_score.net_weekly_points # this accomodates for the scenario that more than one player has max points
                else:
                    break
        self.stdout.write(self.style.SUCCESS('Max points columns updated in Points table'))
