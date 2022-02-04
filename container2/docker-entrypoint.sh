#!/bin/bash

# HiveKeepers - container2 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 28/01/22
# current: 04/02/22
# version: 0.8

function setTimeZone {
    if [ -f "/etc/timezone.host" ]; then
        CLIENT_TIMEZONE=$(cat /etc/timezone)
        HOST_TIMEZONE=$(cat /etc/timezone.host)

        if [ "${CLIENT_TIMEZONE}" != "${HOST_TIMEZONE}" ]; then
            echo "Reconfigure timezone to "${HOST_TIMEZONE}
            echo ${HOST_TIMEZONE} > /etc/timezone
            dpkg-reconfigure -f noninteractive tzdata
        fi
    fi
}

## might want to set tz in compose...
setTimeZone

# cd into app dir
cd /hivekeepers/dash_app/

if [ -s requirements.txt ]
  then
    echo "[ENTRYPOINT] requirements.txt is populated..."

    # setup virtual env
    echo "[ENTRYPOINT] installing venv..."
    python3 -m venv dash-venv

    echo "[ENTRYPOINT] activating venv..."
    source dash-venv/bin/activate

    # update pip
    echo "[ENTRYPOINT] upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel

    # install python requirements
    echo "[ENTRYPOINT] installing requirements..."
    pip install -r requirements.txt

    # set up gunicorn logs and tailing
    echo "[ENTRYPOINT] setting up gunicorn logging..."
    touch gunicorn-logs/access.log
    touch gunicorn-logs/gunicorn.log
    tail -n 0 -f gunicorn-logs/*.log &

    # start dash app
    echo "[ENTRYPOINT] starting application dashboard..."
    exec gunicorn hivekeepers_app:server \
    --name hivekeepers_app \
    --bind 0.0.0.0:8050 \
    --workers 3 \
    --log-level=info \
    --log-file=gunicorn-logs/gunicorn.log \
    --access-logfile=gunicorn-logs/access.log \
    "$@"

  else
    echo "requirements.txt is empty; not running pip..."
fi
