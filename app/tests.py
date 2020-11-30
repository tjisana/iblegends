from django.test import TestCase
from .models import Player

class EplFanstasyTestCase(TestCase):
    def setUp(self):
        Player.objects.create(player_name='Player Name 1', entry_name="Team 1", displayed_name='P1')
        Player.objects.create(player_name='Player Name 2', entry_name="Team 2", displayed_name='P2')
        Player.objects.create(player_name='Player Name 3', entry_name="Team 3", displayed_name='P3')

    def player_count(self):
        self.assertEquals(Player.objects.count(),3)