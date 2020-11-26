from django.shortcuts import render

from .models import Player, Points, WinTotals
from .utils import get_current_event_and_status_from_web, update_points_table_from_web

import requests


def index(request):
    current_event, points_are_final = get_current_event_and_status_from_web()
    all_players = Player.objects.all()
    latest_week_in_db = Points.objects.last().week
    
    if not points_are_final:
        Points.objects.filter(week=current_event).delete()    
    
    if (current_event - latest_week_in_db) > 1:
        print([week for week in range(latest_week_in_db+1, current_event)])
        for week in range(latest_week_in_db+1, current_event):
            update_points_table_from_web(week, True)

    if not(current_event == latest_week_in_db and points_are_final):
        update_points_table_from_web(current_event, points_are_final)


    context = {
        'players': all_players,
        'all_points': Points.objects.weekly_results(),
        'weekly_win_totals': WinTotals.objects.all().order_by('player'),
        }
    return render(request, 'app/index.html', context)