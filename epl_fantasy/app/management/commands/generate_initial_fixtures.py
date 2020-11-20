from django.core.management.base import BaseCommand, CommandError

from app.models import Payment

import json
import os
import requests


class Command(BaseCommand):
    help = 'Generates initial fixture data'

    def __init__(self, *args, **kwargs):
        self.fixture = []
        super().__init__(*args, **kwargs)
    
    def handle(self, *args, **options):        
        url = 'https://fantasy.premierleague.com/api/leagues-classic/984485/standings/?page_new_entries=1&page_standings=1&phase=1'
        response = requests.get(url)        
        for player in response.json()['standings']['results']:
            self.fixture.append(
                {
                    "model": "app.Player",
                    "pk": player['entry'],
                    "fields": {
                        "player_name": player['player_name'],
                        "entry_name": player['entry_name'],
                        "displayed_name": player['player_name']
                    }
                }
            )
            self.fixture.append(
                {
                    "model": "app.Payment",
                    "fields": {                        
                        "player": player['entry'],
                        "paid": True,
                        "method": 'Venmo',
                        "amount": Payment.FANTASY_COST
                        }
                }
            )            

            self.weekly_points(player['entry'])

        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'fixtures', 'players_fixture.json'), 'w') as output:
            json.dump(self.fixture, output)
        self.stdout.write(self.style.SUCCESS('Successfully created fixtures file players_fixture.json'))

    def weekly_points(self, player):
        url = 'https://fantasy.premierleague.com/api/event-status/'
        response = requests.get(url).json()        
        event = response['status'][0]['event']        
        for week_number in range(1, event+1):
            url = f"https://fantasy.premierleague.com/api/entry/{player}/event/{week_number}/picks/"            
            response = requests.get(url).json()            
            self.fixture.append(
                {
                    "model": "app.Points",
                    "fields":{
                        'week': week_number,
                        'player': player,
                        'total_points': response['entry_history']['total_points'],                                        
                        'transfer_cost': response['entry_history']['event_transfers_cost'],
                        'net_weekly_points': response['entry_history']['points'] - response['entry_history']['event_transfers_cost'],
                        'max_points': False
                    }
                }
            )
