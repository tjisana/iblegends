import httpretty

# from django.http import JsonResponse
from django.test import TestCase

from .models import Player, Payment, WinTotals, Points
from .utils import get_current_event_and_status_from_web, update_points_table_from_web

import json


TRANSFER_COST = 4

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
    def test_update_points_table_from_web_simple(self):
        """
            Test Points table is updated
        """

        # WEEK 1 
        httpretty.register_uri(
            httpretty.GET,
            'https://fantasy.premierleague.com/api/event-status/',
            body=json.dumps({"status":
                [
                    {"bonus_added":True,"event":1,"points":"r"},
                    {"bonus_added":True,"event":1,"points":"r"},
                    {"bonus_added":True,"event":1,"points":"r"},
                    {"bonus_added":True,"event":1,"points":"r"}
                ],
                "leagues":"Updated"}
            )
        )

        current_event, points_are_final = get_current_event_and_status_from_web()
        week1_points = [49, 50, 51, 52]  # player 1, 2, 3, 4
        for player, point in zip(Player.objects.all(), week1_points):
            httpretty.register_uri(
                httpretty.GET,
                f"https://fantasy.premierleague.com/api/entry/{player.id}/event/{current_event}/picks/",
                body=json.dumps(
                    {"active_chip":None,"automatic_subs":[],"entry_history":{"event":1,"points":point,"total_points":point,"event_transfers":0,"event_transfers_cost":0}}
                )
            )        
        
        update_points_table_from_web(current_event, points_are_final)
        player4_week1_points = Points.objects.get(week=1, player__displayed_name='P4') 

        self.assertEquals(player4_week1_points.total_points, week1_points[3])
        self.assertEquals(player4_week1_points.transfer_cost, 0)
        self.assertEquals(player4_week1_points.final_points, points_are_final)
        self.assertEquals(player4_week1_points.net_weekly_points, week1_points[3])
        #  not sure yet if I want to include the below asserts in this test. since they are changed by update_weekly_winner() and not update_points_table_from_web()
        # self.assertTrue(Points.objects.get(week=1, player__displayed_name='P4').current_leader)
        # self.assertEquals(Points.objects.get(week=1, player__displayed_name='P4').weekly_winner, 'P4')

    @httpretty.activate
    def test_update_points_table_from_web_multiple_weeks(self):
        """
            Test Points table is updated with more than one week of data
        """
        # WEEK 1
        week1_points = [49, 50, 51, 52]  # player 1, 2, 3, 4    
        for player, point in zip(Player.objects.all(), week1_points):
            Points.objects.create(week=1, player=player, total_points=point, transfer_cost=0, final_points=True, net_weekly_points=point, max_points=False, current_leader=False)
        player4_week1 = Points.objects.get(week=1, player__displayed_name='P4')
        player4_week1.max_points=True
        player4_week1.current_leader=True

        # WEEK 2 
        httpretty.register_uri(
            httpretty.GET,
            'https://fantasy.premierleague.com/api/event-status/',
            body=json.dumps({"status":
                [
                    {"bonus_added":True,"event":2,"points":"r"},
                    {"bonus_added":True,"event":2,"points":"r"},
                    {"bonus_added":True,"event":2,"points":"r"},
                    {"bonus_added":True,"event":2,"points":"r"}
                ],
                "leagues":"Updated"}
            )
        )

        current_event, points_are_final = get_current_event_and_status_from_web()
        week2_points = [49, 50, 51, 52]  # Week 2 points for player 1, 2, 3, 4
        transfers = [0, 1, 2, 0]  # Week 2 transfer_cost for player 1, 2, 3, 4
        week2_total_points = [x + y - z * TRANSFER_COST for x, y, z in zip(week1_points, week2_points, transfers)]
        for player, point, transfer, week2_total in zip(Player.objects.all(), week2_points, transfers, week2_total_points):
            httpretty.register_uri(
                httpretty.GET,
                f"https://fantasy.premierleague.com/api/entry/{player.id}/event/{current_event}/picks/",
                body=json.dumps(
                    {"active_chip":None,"automatic_subs":[],"entry_history":{"event":current_event,"points":point,"total_points":week2_total,"event_transfers":transfer,"event_transfers_cost":transfer * TRANSFER_COST}}
                )
            )        
        
        update_points_table_from_web(current_event, points_are_final)
        for point_in_db, week2_point_from_web, transfer in zip(Points.objects.filter(week=current_event).order_by('player__displayed_name'), week2_points, transfers):            
            self.assertEquals(point_in_db.net_weekly_points, week2_point_from_web - transfer * TRANSFER_COST)
                
    @httpretty.activate
    def test_update_points_table_from_web_week1(self):
        """
            Simple first test to ensure week1 results are correctly imported into the database and tables are updated.
        """
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
        """
            What if two people have the same exact weekly score
        """
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
        self.assertEquals(player4_wintotals.winnings, WinTotals.WEEKLY_PRIZE / 2)
        self.assertEquals(player4_wintotals.total_winnings, WinTotals.WEEKLY_PRIZE / 2) 