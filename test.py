import requests
event_status = 'https://fantasy.premierleague.com/api/event-status/'
response = requests.get(event_status)
event = response.json()['status'][0]['event']

url = 'https://fantasy.premierleague.com/api/leagues-classic/984485/standings/?page_new_entries=1&page_standings=1&phase=1'
response = requests.get(url)

for player in response.json()['standings']['results']:
    entry_id = player['entry']
    picks_url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{event}/picks/"
    event_info = requests.get(picks_url)
    transfer_cost = event_info.json()['entry_history']['event_transfers_cost']

    print(f"event total {player['event_total']}, player {player['player_name']}, rank {player['rank']}, transfer_cost {transfer_cost}, net_score {player['event_total'] - transfer_cost}, total_score {player['total']}")
    
    