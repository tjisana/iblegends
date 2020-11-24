from django.shortcuts import render

from .models import Player, Points

def index(request):
    players = Player.objects.all()
    all_points = Points.objects.weekly_results()
    
    context = {
        'players': players,
        'all_points': all_points
        }
    return render(request, 'app/index.html', context)