from django.shortcuts import render

from .models import Player, Points

import requests

def db_contains_latest_data():
    latest_week_in_db = Points.objects.last().week
    url = 'https://fantasy.premierleague.com/api/event-status/'
    response = requests.get(url).json()
    event = response['status'][0]['event']
    return event == latest_week_in_db

def index(request):
    print(db_contains_latest_data())
    players = Player.objects.all()
    all_points = Points.objects.weekly_results()
    
    context = {
        'players': players,
        'all_points': all_points
        }
    return render(request, 'app/index.html', context)