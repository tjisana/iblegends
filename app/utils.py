from .models import Points, Player, WinTotals

import decimal
import json
import os
import requests


def get_current_event_and_status_from_web():
    url = 'https://fantasy.premierleague.com/api/event-status/'
    response = requests.get(url).json()
    statuses = [status['bonus_added'] and status['points']=='r' for status in response['status']]
    return response['status'][0]['event'], (all(statuses) and response['leagues'] != 'Updating')
    #  return current event week. Also return check if points are final by looking at status

def update_current_leader(week_number: int) -> None:
    max_total_points = -1000
    for player_total_score in Points.objects.filter(week=week_number).order_by('-total_points'):
        if player_total_score.total_points >= max_total_points:
            player_total_score.current_leader = True
            player_total_score.save()
            max_total_points = player_total_score.total_points # this accomodates for the scenario that more than one player is current leader
        else:
            break

def get_captain_vice_captain_bench_points(all_footballers_week_points: dict, week: int, point: Points, players_current_rank: dict) -> tuple:
    url = f"https://fantasy.premierleague.com/api/entry/{point.player.id}/event/{week}/picks/"
    picks = requests.get(url).json()['picks']

    bench_points = 0
    for pick in picks:
        if pick['is_captain']:
            captain_points = all_footballers_week_points['elements'][pick['element']-1]['stats']['total_points'] * pick['multiplier']
        elif pick['is_vice_captain']:
            vice_captain_points = all_footballers_week_points['elements'][pick['element']-1]['stats']['total_points'] * pick['multiplier']
        elif pick['multiplier'] == 0:
            bench_points+=all_footballers_week_points['elements'][pick['element']-1]['stats']['total_points'] * 1
    return point, captain_points, vice_captain_points, bench_points, players_current_rank[point.player.id]

def weekly_winner_tie_breaker(this_week_winners_points: Points):
    """
        1. Captain points
        2. VC points
        3. Total bench boints
        4. Whoever is higher in the table
    """
    cap_vice_bench_points = []
    current_week = this_week_winners_points[0].week
    url = f"https://fantasy.premierleague.com/api/event/{current_week}/live/"
    all_footballers_week_points = requests.get(url).json()
    players_current_rank = {point.player.id: -1 * index for index, point in enumerate(Points.objects.filter(week=current_week).order_by('-total_points'), start=1)}
    for point in this_week_winners_points:
        cap_vice_bench_points.append(get_captain_vice_captain_bench_points(all_footballers_week_points, current_week, point, players_current_rank))

    for point in sorted(cap_vice_bench_points, key=lambda e: (e[1], e[2], e[3], e[4]))[:-1]:
        point[0].max_points = False
        point[0].save()

def update_weekly_winner(week_number: int):
    max_net_weekly_points = -1000

    for player_weekly_score in Points.objects.filter(week=week_number).order_by('-net_weekly_points'):
        if player_weekly_score.net_weekly_points >= max_net_weekly_points:
            player_weekly_score.max_points = True
            player_weekly_score.save()
            max_net_weekly_points = player_weekly_score.net_weekly_points # this accomodates for the scenario that more than one player has max points
        else:
            break

    update_current_leader(week_number)
    this_week_winners_points = Points.objects.filter(week=week_number, max_points=True)

    if this_week_winners_points.count() > 1:
        weekly_winner_tie_breaker(this_week_winners_points)
        this_week_winners_points = Points.objects.filter(week=week_number, max_points=True)

    this_week_winner = WinTotals.objects.get(player=this_week_winners_points[0].player)
    this_week_winner.weekly_wins += 1
    this_week_winner.winnings += decimal.Decimal(WinTotals.WEEKLY_PRIZE)
    this_week_winner.total_winnings += decimal.Decimal(WinTotals.WEEKLY_PRIZE)
    this_week_winner.save()

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
                'max_points': False,
                'current_leader': False,
                'overall_rank': response['entry_history']['overall_rank']
                }
        )
    if points_are_final:
        update_weekly_winner(current_event)
    else:
        update_current_leader(current_event)