from django.shortcuts import render

from .models import Player, Points
from .utils import get_current_event_and_status_from_web, update_points_table_from_web

import requests


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