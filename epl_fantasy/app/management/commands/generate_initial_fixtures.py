from django.core.management.base import BaseCommand, CommandError

from app.models.Payment import FANTASY_COST

import json
import os
import requests


class Command(BaseCommand):
    help = 'Generates initial fixture data'    

    def handle(self, *args, **options):        
        url = 'https://fantasy.premierleague.com/api/leagues-classic/984485/standings/?page_new_entries=1&page_standings=1&phase=1'
        response = requests.get(url)
        fixture = []
        for player in response.json()['standings']['results']:
            fixture.append(
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
            fixture.append(
                {
                    "model": "app.Payment",                    
                    "fields": {                        
                        "player": player['entry'],
                        "paid": True,
                        "method": 'Venmo',
                        "amount": FANTASY_COST
                        }
                }
            )
        
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'fixtures', 'players_fixture.json'), 'w') as output:
            json.dump(fixture, output)
        self.stdout.write(self.style.SUCCESS('Successfully created fixtures file players_fixture.json'))