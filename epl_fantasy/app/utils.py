from .models import Points, Player

import json
import os
import requests


def get_current_event_and_status_from_web():
    url = 'https://fantasy.premierleague.com/api/event-status/'
    response = requests.get(url).json()        
    statuses = [status['bonus_added'] and status['points']=='r' for status in response['status']]    
    return response['status'][0]['event'], (all(statuses) and response['leagues'] != 'Updating')
    #  return current event week. Also return check if points are final by looking at status

def update_weekly_winner(week_number):
    max_net_weekly_points = -1000
    for player_weekly_score in Points.objects.filter(week=week_number).order_by('-net_weekly_points'):
        if player_weekly_score.net_weekly_points >= max_net_weekly_points:
            player_weekly_score.max_points = True
            player_weekly_score.save()
            max_net_weekly_points = player_weekly_score.net_weekly_points # this accomodates for the scenario that more than one player has max points
        else:
            break

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
    if points_are_final:
        update_weekly_winner(current_event)