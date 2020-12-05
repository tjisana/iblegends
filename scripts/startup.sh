#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${DIR}/../../venv/bin/activate
python ${DIR}/../manage.py flush --noinput
python ${DIR}/../manage.py generate_initial_fixtures
python ${DIR}/../manage.py loaddata players_fixture
python ${DIR}/../manage.py populate_wintotals
