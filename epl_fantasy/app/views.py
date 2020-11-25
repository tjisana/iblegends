from django.shortcuts import render

from .models import Player, Points
from .utils import get_current_event_and_status_from_web

import requests


def update_points_table_from_web(current_event, points_are_final):
    all_players = Player.objects.all()
    for player in all_players:
        url = f"https://fantasy.premierleague.com/api/entry/{player.id}/event/{current_event}/picks/"
        response = requests.get(url).json()
        Points.objects.create(
            **{
                'week': current_event,
                'player': player,
                'total_points': response['entry_history']['total_points'],   
                'transfer_cost': response['entry_history']['event_transfers_cost'],
                'final_points': points_are_final,
                'net_weekly_points': response['entry_history']['points'] - response['entry_history']['event_transfers_cost'],
                'max_points': False
                }
        )

def index(request):
    current_event, points_are_final = get_current_event_and_status_from_web()
    all_players = Player.objects.all()
    
    if not points_are_final:
        Points.objects.filter(week=current_event).delete()
    
    if not(current_event == Points.objects.last().week and points_are_final):
        update_points_table_from_web(current_event, points_are_final)


    context = {
        'players': all_players,
        'all_points': Points.objects.weekly_results()
        }
    return render(request, 'app/index.html', context)