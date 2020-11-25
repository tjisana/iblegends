import json
import os
import requests


def get_current_event_and_status_from_web():
    url = 'https://fantasy.premierleague.com/api/event-status/'
    response = requests.get(url).json()        
    statuses = [status['bonus_added'] and status['points']=='r' for status in response['status']]    
    return response['status'][0]['event'], (all(statuses) and response['leagues'] != 'Updating')
    #  return current event week. Also return check if points are final by looking at status