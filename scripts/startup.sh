source ../../venv/bin/activate
python ../epl_fantasy/manage.py flush --noinput
python ../epl_fantasy/manage.py generate_initial_fixtures
python ../epl_fantasy/manage.py loaddata players_fixture