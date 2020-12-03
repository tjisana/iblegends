import httpretty

# from django.http import JsonResponse
from django.test import TestCase

from .models import Player, Payment, WinTotals, Points
from .utils import get_current_event_and_status_from_web, update_points_table_from_web

import json


class EplFanstasyTestCase(TestCase):
    def setUp(self):
        Player.objects.create(player_name='Player Name 1', entry_name="Team 1", displayed_name='P1')
        Player.objects.create(player_name='Player Name 2', entry_name="Team 2", displayed_name='P2')
        Player.objects.create(player_name='Player Name 3', entry_name="Team 3", displayed_name='P3')
        Player.objects.create(player_name='Player Name 4', entry_name="Team 4", displayed_name='P4')
        
        for player in Player.objects.all():
            Payment.objects.create(player=player, paid=True, method='Venmo', amount=Payment.FANTASY_COST)
            WinTotals.objects.create(player=player, weekly_wins=0, winnings=0, season_winner=False, total_winnings=0)  
        
    @httpretty.activate
    def test_get_current_event_and_status_from_web(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://fantasy.premierleague.com/api/event-status/',
            body=json.dumps({"status":
            [
                {"bonus_added":True,"date":"2020-11-27","event":9,"points":"r"},
                {"bonus_added":True,"date":"2020-11-28","event":9,"points":"r"},
                {"bonus_added":True,"date":"2020-11-29","event":9,"points":"r"},
                {"bonus_added":True,"date":"2020-11-30","event":9,"points":"r"}],"leagues":"Updated"}
            )
        )
        current_event, points_are_final = get_current_event_and_status_from_web()
        self.assertEqual(current_event, 9)
        self.assertEqual(points_are_final, True)
    
    @httpretty.activate
    def test_update_points_table_from_web_week1(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://fantasy.premierleague.com/api/event-status/',
            body=json.dumps({"status":
            [
                {"bonus_added":True,"date":"2020-11-27","event":1,"points":"r"},
                {"bonus_added":True,"date":"2020-11-28","event":1,"points":"r"},
                {"bonus_added":True,"date":"2020-11-29","event":1,"points":"r"},
                {"bonus_added":True,"date":"2020-11-30","event":1,"points":"r"}],"leagues":"Updated"}
            )
        )

        current_event, points_are_final = get_current_event_and_status_from_web()
        points = [49, 50, 51, 52]
        for player, point in zip(Player.objects.all(), points):
            httpretty.register_uri(
                httpretty.GET,
                f"https://fantasy.premierleague.com/api/entry/{player.id}/event/{current_event}/picks/",
                body=json.dumps(
                    {"active_chip":None,"automatic_subs":[],"entry_history":{"event":1,"points":point,"total_points":point,"event_transfers":0,"event_transfers_cost":0}}
                )
            )        
        update_points_table_from_web(current_event, points_are_final)
        self.assertTrue(Points.objects.get(week=1, player__displayed_name='P4').max_points)
        self.assertTrue(Points.objects.get(week=1, player__displayed_name='P4').current_leader)
        self.assertEquals(Points.objects.get(week=1, player__displayed_name='P4').weekly_winner, 'P4')

        
        player4_wintotals = WinTotals.objects.get(player=Player.objects.get(displayed_name='P4'))
        self.assertEquals(player4_wintotals.weekly_wins, 1)
        self.assertEquals(player4_wintotals.winnings, WinTotals.WEEKLY_PRIZE)
        self.assertEquals(player4_wintotals.total_winnings, WinTotals.WEEKLY_PRIZE)

    
    @httpretty.activate
    def test_update_points_table_from_web_multiple_weekly_winners(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://fantasy.premierleague.com/api/event-status/',
            body=json.dumps({"status":
            [
                {"bonus_added":True,"date":"2020-11-27","event":1,"points":"r"},
                {"bonus_added":True,"date":"2020-11-28","event":1,"points":"r"},
                {"bonus_added":True,"date":"2020-11-29","event":1,"points":"r"},
                {"bonus_added":True,"date":"2020-11-30","event":1,"points":"r"}],"leagues":"Updated"}
            )
        )

        current_event, points_are_final = get_current_event_and_status_from_web()
        points = [49, 50, 52, 52]
        for player, point in zip(Player.objects.all(), points):
            httpretty.register_uri(
                httpretty.GET,
                f"https://fantasy.premierleague.com/api/entry/{player.id}/event/{current_event}/picks/",
                body=json.dumps(
                    {"active_chip":None,"automatic_subs":[],"entry_history":{"event":1,"points":point,"total_points":point,"event_transfers":0,"event_transfers_cost":0}}
                )
            )        
        update_points_table_from_web(current_event, points_are_final)
        self.assertTrue(Points.objects.get(week=1, player__displayed_name='P4').max_points)
        self.assertTrue(Points.objects.get(week=1, player__displayed_name='P4').current_leader)
        self.assertEquals(Points.objects.get(week=1, player__displayed_name='P4').weekly_winner, 'P3,P4')

        self.assertTrue(Points.objects.get(week=1, player__displayed_name='P3').max_points)
        self.assertTrue(Points.objects.get(week=1, player__displayed_name='P3').current_leader)
        self.assertEquals(Points.objects.get(week=1, player__displayed_name='P3').weekly_winner, 'P3,P4')

        
        player4_wintotals = WinTotals.objects.get(player=Player.objects.get(displayed_name='P4'))
        self.assertEquals(player4_wintotals.weekly_wins, 1)
        self.assertEquals(player4_wintotals.winnings, WinTotals.WEEKLY_PRIZE)
        self.assertEquals(player4_wintotals.total_winnings, WinTotals.WEEKLY_PRIZE)