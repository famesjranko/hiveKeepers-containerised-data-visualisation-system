#!/bin/bash

# HiveKeepers - container2 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 28/01/22
# current: 25/02/22
# version: 0.81

# get relevant environment variables, otherwise use defaults
user="${GUNICORN_UID:-1000}" # 1005 default from gunicorn docs
group="${GUNICORN_GID:-1000}" # 205 default from gunicorn docs
name="${GUNICORN_NAME:-hivekeepers_app}"
workers="${GUNICORN_WORKERS:-1}"
port="${GUNICORN_PORT:-8050}"
log_level="${GUNICORN_LOGLEVEL:-info}"
threads=$((2*$workers)) # set threads to twice the workers

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

# set up gunicorn logs and tailing
#echo "[ENTRYPOINT] setting up gunicorn logging..."
#touch gunicorn-logs/access.log
#touch gunicorn-logs/gunicorn.log
#tail -n 0 -f gunicorn-logs/*.log &

# cd into app dir
cd /home/hivekeeper/dash_app/

# check if files exist and have content
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
    touch /home/hivekeeper/gunicorn-logs/access.log
    touch /home/hivekeeper/gunicorn-logs/gunicorn.log
    tail -n 0 -f /home/hivekeeper/gunicorn-logs/*.log &

    # create sql database file
    # if [[ -f data.csv ]] && [[ -f update_db.py ]]; then
    #   echo "[ENTRYPOINT] found CSV file!"
    #   echo "[ENTRYPOINT] building database..."
    #   python update_db.py

    if [ -f startup_update_db.py ]; then
      echo "[ENTRYPOINT] found update db script file!"
      echo "[ENTRYPOINT] building database..."
      python startup_update_db.py
      
      if [ -f hivekeepers.db ]; then
        echo "[ENTRYPOINT] database created!"
      else
        echo "[ENTRYPOINT] [ERROR] database missing!"
      fi
    else
      echo "[ENTRYPOINT] [ERROR] startup_update_db.py NOT found!"
    fi

    # start dash app via wsgi (gunicorn)
    echo "[ENTRYPOINT] starting application dashboard..."
    exec gunicorn app:server \
    --user $user \
    --group $group \
    --name "$name" \
    --bind 0.0.0.0:$port \
    --workers $workers \
    --worker-tmp-dir /dev/shm \
    --threads $threads \
    --log-level="$log_level" \
    --log-file=/home/hivekeeper/gunicorn-logs/gunicorn.log \
    --access-logfile=/home/hivekeeper/gunicorn-logs/access.log \
    "$@"

  else
    echo "[ENTRYPOINT] requirements.txt NOT found!"
    echo "[ENTRYPOINT] app.py NOT found!"
    echo "[ENTRYPOINT] NOT running python installation..."
fi
