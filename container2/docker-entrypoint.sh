#!/bin/bash

# HiveKeepers - container2 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 28/01/22
# current: 04/02/22
# version: 0.8

# get relevant environment variables, otherwise use defaults
user="${GUNICORN_UID:-1005}" # 1005 default from gunicorn docs
group="${GUNICORN_GID:-205}" # 205 default from gunicorn docs
name="${GUNICORN_NAME:-hivekeepers_app}"
workers="${GUNICORN_WORKERS:-1}"
port="${GUNICORN_PORT:-8050}"
log_level="${GUNICORN_LOGLEVEL:-info}"

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
cd /dash_app/

if [[ -s requirements.txt && -s app.py ]]
  then
    echo "[ENTRYPOINT] requirements.txt is populated!"
    echo "[ENTRYPOINT] app.py is populated!"
    echo "[ENTRYPOINT] starting python installation..."

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
    touch /gunicorn-logs/access.log
    touch /gunicorn-logs/gunicorn.log
    tail -n 0 -f /gunicorn-logs/*.log &

    # start dash app via wsgi (gunicorn)
    echo "[ENTRYPOINT] starting application dashboard..."
    exec gunicorn app:server \
    --user $user \
    --group $group \
    --name "$name" \
    --bind 0.0.0.0:$port \
    --workers $workers \
    --log-level="$log_level" \
    --log-file=/gunicorn-logs/gunicorn.log \
    --access-logfile=/gunicorn-logs/access.log \
    "$@"

  else
    echo "[ENTRYPOINT] requirements.txt NOT populated!"
    echo "[ENTRYPOINT] app.py NOT populated!"
    echo "[ENTRYPOINT] NOT running python installation..."
fi
