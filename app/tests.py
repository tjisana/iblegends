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

        self.players = [player for player in Player.objects.all()]
        for player in self.players:
            Payment.objects.create(player=player, paid=True, method='Venmo', amount=Payment.FANTASY_COST)
            WinTotals.objects.create(player=player, weekly_wins=0, winnings=0, season_winner=False, total_winnings=0)

    def setup_week_data(self, week_number: int, points: list, total_points: list, event_transfers: list, overall_ranks: list, player_picks: dict = None):
        httpretty.register_uri(
            httpretty.GET,
            'https://fantasy.premierleague.com/api/event-status/',
            body=json.dumps({"status":
                [
                    {"bonus_added":True,"event":week_number,"points":"r"},
                    {"bonus_added":True,"event":week_number,"points":"r"},
                    {"bonus_added":True,"event":week_number,"points":"r"},
                    {"bonus_added":True,"event":week_number,"points":"r"}
                ],
                "leagues":"Updated"}
            )
        )

        httpretty.register_uri(
            httpretty.GET,
            f"https://fantasy.premierleague.com/api/event/{week_number}/live/",
            body=json.dumps({"elements":
                [
                    {"id":1,"stats":{"total_points":1}},
                    {"id":2,"stats":{"total_points":2}},
                    {"id":3,"stats":{"total_points":3}},
                    {"id":4,"stats":{"total_points":4}},
                    {"id":5,"stats":{"total_points":5}},
                    {"id":6,"stats":{"total_points":6}},
                    {"id":7,"stats":{"total_points":7}},
                    {"id":8,"stats":{"total_points":8}},
                    {"id":9,"stats":{"total_points":9}},
                    {"id":10,"stats":{"total_points":10}},
                ]}
            )
        )

        for player, point, total_point, event_transfer, overall_rank in zip(Player.objects.all(), points, total_points, event_transfers, overall_ranks):
            picks = {"active_chip":None,"automatic_subs":[],"entry_history":{
                        "event":week_number,
                        "points":point,
                        "total_points":total_point,
                        "event_transfers":event_transfer,
                        "event_transfers_cost":event_transfer * Points.TRANSFER_POINTS_COST,
                        "overall_rank":overall_rank}}
            if player_picks:
                picks['picks'] = player_picks[player]

            httpretty.register_uri(
                httpretty.GET,
                f"https://fantasy.premierleague.com/api/entry/{player.id}/event/{week_number}/picks/",
                body=json.dumps(picks)
            )

    def setup_week1_data(self):
        self.total_points = self.points = (49, 50, 51, 52)
        self.event_transfers = (0,0,0,0)
        self.overall_ranks = (4,3,2,1)
        self.setup_week_data(week_number=1, points=self.points, total_points=self.total_points, event_transfers=self.event_transfers, overall_ranks=self.overall_ranks)

    def setup_week2_data(self):
        week1_points = (49, 50, 51, 52)
        self.points = (49, 50, 51, 52)
        self.event_transfers = (0,1,2,0)
        self.total_points = [x + y - z * Points.TRANSFER_POINTS_COST for x, y, z in zip(week1_points, self.points, self.event_transfers)]
        self.overall_ranks = (2, 3, 4, 1)
        self.setup_week_data(week_number=2, points=self.points, total_points=self.total_points, event_transfers=self.event_transfers, overall_ranks=self.overall_ranks)


    @httpretty.activate
    def test_get_current_event_and_status_from_web(self):
        """
            Test function get_current_event_and_status_from_web. Should return current event and point_are_final:bool
        """
        self.setup_week1_data()
        current_event, points_are_final = get_current_event_and_status_from_web()
        self.assertEqual(current_event, 1)
        self.assertEqual(points_are_final, True)

    @httpretty.activate
    def test_update_points_table_from_web_simple(self):
        """
            Test Points table is updated
        """
        self.setup_week1_data()
        current_event, points_are_final = get_current_event_and_status_from_web()
        update_points_table_from_web(current_event, points_are_final)
        player4_week1_points = Points.objects.get(week=1, player__displayed_name='P4')

        self.assertEqual(player4_week1_points.total_points, self.points[3])
        self.assertEqual(player4_week1_points.transfer_cost, 0)
        self.assertEqual(player4_week1_points.final_points, points_are_final)
        self.assertEqual(player4_week1_points.net_weekly_points, self.points[3])
        #  not sure yet if I want to include the below asserts in this test. since they are changed by update_weekly_winner() and not update_points_table_from_web()
        # self.assertTrue(Points.objects.get(week=1, player__displayed_name='P4').current_leader)
        # self.assertEqual(Points.objects.get(week=1, player__displayed_name='P4').weekly_winner, 'P4')

    @httpretty.activate
    def test_update_points_table_from_web_multiple_weeks(self):
        """
            Test Points table is updated with more than one week of data
        """
        self.setup_week1_data()
        update_points_table_from_web(1, True)
        self.setup_week2_data()
        update_points_table_from_web(2, True)
        for point_in_db, week2_point_from_web, transfer in zip(Points.objects.filter(week=2).order_by('player__displayed_name'), self.points, self.event_transfers):
            self.assertEqual(point_in_db.net_weekly_points, week2_point_from_web - transfer * Points.TRANSFER_POINTS_COST)

    @httpretty.activate
    def test_update_weekly_winner(self):
        """
            Testing that max_points, current_leader and WinTotals table are correctly updated
        """
        self.setup_week1_data()
        current_event, points_are_final = get_current_event_and_status_from_web()
        update_points_table_from_web(current_event, points_are_final)

        week1_winner = Points.objects.get(week=1, player__displayed_name='P4')
        self.assertTrue(week1_winner.max_points)
        self.assertTrue(week1_winner.current_leader)
        self.assertEqual(week1_winner.weekly_winner, 'P4')

        player4_wintotals = WinTotals.objects.get(player=Player.objects.get(displayed_name='P4'))
        self.assertEqual(player4_wintotals.weekly_wins, 1)
        self.assertEqual(player4_wintotals.winnings, WinTotals.WEEKLY_PRIZE)
        self.assertEqual(player4_wintotals.total_winnings, WinTotals.WEEKLY_PRIZE)

        self.setup_week2_data()
        current_event, points_are_final = get_current_event_and_status_from_web()
        update_points_table_from_web(current_event, points_are_final)
        self.assertEqual(Points.objects.get(week=2, player__displayed_name='P2').current_leader, False)
        self.assertTrue(Points.objects.get(week=2, player__displayed_name='P4').current_leader)
        self.assertTrue(Points.objects.get(week=2, player__displayed_name='P4').max_points)

        self.assertEqual(WinTotals.objects.get(player__displayed_name='P4').weekly_wins, 2)
        self.assertEqual(WinTotals.objects.get(player__displayed_name='P4').winnings, 2 * WinTotals.WEEKLY_PRIZE)


    @httpretty.activate
    def test_update_points_table_from_web_multiple_weekly_winners_rule1(self):
        """
            What if two people have the same exact weekly score.Tie breaker rules are:
            1. Captain points
            2. VC points
            3. Total bench boints
            4. Whoever is higher in the table
        """
        p1, p2, p3, p4 = self.players
        self.total_points = self.points = (49, 50, 52, 52)
        self.event_transfers = (0,0,0,0)
        self.overall_ranks = (4,3,2,1)
        self.setup_week_data(
            week_number=1,
            points=self.points,
            total_points=self.total_points,
            event_transfers=self.event_transfers,
            overall_ranks=self.overall_ranks,
            player_picks={
                p1: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p2: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p3: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p4: [
                    {'element': 1, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 2, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
            }
        )
        current_event, points_are_final = get_current_event_and_status_from_web()
        update_points_table_from_web(current_event, points_are_final)

        week1_player4_points = Points.objects.get(week=1, player__displayed_name='P4')
        week1_player3_points = Points.objects.get(week=1, player__displayed_name='P3')

        self.assertTrue(week1_player3_points.max_points)
        self.assertFalse(week1_player4_points.max_points)
        self.assertTrue(week1_player3_points.current_leader)
        self.assertTrue(week1_player4_points.current_leader)
        self.assertEqual(week1_player4_points.weekly_winner, 'P3')

        player3_wintotals = WinTotals.objects.get(player=Player.objects.get(displayed_name='P3'))
        self.assertEqual(player3_wintotals.weekly_wins, 1)
        self.assertEqual(player3_wintotals.winnings, WinTotals.WEEKLY_PRIZE)

    @httpretty.activate
    def test_update_points_table_from_web_multiple_weekly_winners_rule2(self):
        """
            What if two people have the same exact weekly score.Tie breaker rules are:
            1. Captain points
            2. VC points
            3. Total bench boints
            4. Whoever is higher in the table
        """
        p1, p2, p3, p4 = self.players
        self.total_points = self.points = (49, 50, 52, 52)
        self.event_transfers = (0,0,0,0)
        self.overall_ranks = (4,3,2,1)
        self.setup_week_data(
            week_number=1,
            points=self.points,
            total_points=self.total_points,
            event_transfers=self.event_transfers,
            overall_ranks=self.overall_ranks,
            player_picks={
                p1: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p2: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p3: [
                    {'element': 1, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 2, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p4: [
                    {'element': 1, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 2, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 6, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
            }
        )
        current_event, points_are_final = get_current_event_and_status_from_web()
        update_points_table_from_web(current_event, points_are_final)

        week1_player4_points = Points.objects.get(week=1, player__displayed_name='P4')
        week1_player3_points = Points.objects.get(week=1, player__displayed_name='P3')

        self.assertFalse(week1_player3_points.max_points)
        self.assertTrue(week1_player4_points.max_points)
        self.assertTrue(week1_player3_points.current_leader)
        self.assertTrue(week1_player4_points.current_leader)
        self.assertEqual(week1_player4_points.weekly_winner, 'P4')

        player3_wintotals = WinTotals.objects.get(player=Player.objects.get(displayed_name='P3'))
        self.assertEqual(player3_wintotals.weekly_wins, 0)
        self.assertEqual(player3_wintotals.winnings, 0)

        player4_wintotals = WinTotals.objects.get(player=Player.objects.get(displayed_name='P4'))
        self.assertEqual(player4_wintotals.weekly_wins, 1)
        self.assertEqual(player4_wintotals.winnings, WinTotals.WEEKLY_PRIZE)

    @httpretty.activate
    def test_update_points_table_from_web_multiple_weekly_winners_rule3(self):
        """
            What if two people have the same exact weekly score.Tie breaker rules are:
            1. Captain points
            2. VC points
            3. Total bench boints
            4. Whoever is higher in the table
        """
        p1, p2, p3, p4 = self.players
        self.total_points = self.points = (49, 50, 52, 52)
        self.event_transfers = (0,0,0,0)
        self.overall_ranks = (4,3,2,1)
        self.setup_week_data(
            week_number=1,
            points=self.points,
            total_points=self.total_points,
            event_transfers=self.event_transfers,
            overall_ranks=self.overall_ranks,
            player_picks={
                p1: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p2: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p3: [
                    {'element': 1, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 2, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p4: [
                    {'element': 1, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 2, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 6, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
            }
        )
        current_event, points_are_final = get_current_event_and_status_from_web()
        update_points_table_from_web(current_event, points_are_final)

        week1_player4_points = Points.objects.get(week=1, player__displayed_name='P4')
        week1_player3_points = Points.objects.get(week=1, player__displayed_name='P3')

        self.assertFalse(week1_player3_points.max_points)
        self.assertTrue(week1_player4_points.max_points)
        self.assertTrue(week1_player3_points.current_leader)
        self.assertTrue(week1_player4_points.current_leader)
        self.assertEqual(week1_player4_points.weekly_winner, 'P4')

        player3_wintotals = WinTotals.objects.get(player=Player.objects.get(displayed_name='P3'))
        self.assertEqual(player3_wintotals.weekly_wins, 0)
        self.assertEqual(player3_wintotals.winnings, 0)

        player4_wintotals = WinTotals.objects.get(player=Player.objects.get(displayed_name='P4'))
        self.assertEqual(player4_wintotals.weekly_wins, 1)
        self.assertEqual(player4_wintotals.winnings, WinTotals.WEEKLY_PRIZE)

    @httpretty.activate
    def test_update_points_table_from_web_multiple_weekly_winners_rule4(self):
        """
            What if two people have the same exact weekly score.Tie breaker rules are:
            1. Captain points
            2. VC points
            3. Total bench boints
            4. Whoever is higher in the table
        """
        p1, p2, p3, p4 = self.players
        self.total_points = self.points = (49, 50, 51, 52)
        self.event_transfers = (0,0,0,0)
        self.overall_ranks = (4,3,2,1)
        self.setup_week_data(
            week_number=1,
            points=self.points,
            total_points=self.total_points,
            event_transfers=self.event_transfers,
            overall_ranks=self.overall_ranks
        )
        current_event, points_are_final = get_current_event_and_status_from_web()
        update_points_table_from_web(current_event, points_are_final)

        self.total_points = self.points = (49, 50, 52, 52)
        self.event_transfers = (0,0,0,0)
        self.overall_ranks = (4,3,2,1)
        self.setup_week_data(
            week_number=2,
            points=self.points,
            total_points=self.total_points,
            event_transfers=self.event_transfers,
            overall_ranks=self.overall_ranks,
            player_picks={
                p1: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p2: [
                    {'element': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 2, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p3: [
                    {'element': 1, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 2, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
                p4: [
                    {'element': 1, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False},
                    {'element': 2, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': True},
                    {'element': 3, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 4, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False},
                    {'element': 5, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False}],
            }
        )
        current_event, points_are_final = get_current_event_and_status_from_web()
        update_points_table_from_web(current_event, points_are_final)

        week1_player4_points = Points.objects.get(week=1, player__displayed_name='P4')
        week1_player3_points = Points.objects.get(week=1, player__displayed_name='P3')

        self.assertFalse(week1_player3_points.max_points)
        self.assertTrue(week1_player4_points.max_points)
        self.assertFalse(week1_player3_points.current_leader)
        self.assertTrue(week1_player4_points.current_leader)
        self.assertEqual(week1_player4_points.weekly_winner, 'P4')