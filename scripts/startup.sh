#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${DIR}/../../venv/bin/activate
python ${DIR}/../epl_fantasy/manage.py flush --noinput
python ${DIR}/../epl_fantasy/manage.py generate_initial_fixtures
python ${DIR}/../epl_fantasy/manage.py loaddata players_fixture