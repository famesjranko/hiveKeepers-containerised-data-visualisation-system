#!/bin/bash

# HiveKeepers - container2 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 28/01/22
# current: 25/02/22
# version: 0.81

# get relevant environment variables, otherwise use defaults
workers="${APP_WORKERS:-1}"
port="${APP_PORT:-8050}"
log_level="${APP_LOG_LEVEL:-info}"
threads=$((2*$workers)) # set threads to twice the workers

function setTimeZone {
  if [ -f "/etc/timezone.host" ]
    then
      CLIENT_TIMEZONE=$(cat /etc/timezone)
      HOST_TIMEZONE=$(cat /etc/timezone.host)

    if [ "${CLIENT_TIMEZONE}" != "${HOST_TIMEZONE}" ]
      then
        echo "Reconfigure timezone to "${HOST_TIMEZONE}
        echo ${HOST_TIMEZONE} > /etc/timezone
        dpkg-reconfigure -f noninteractive tzdata
    fi
  fi
}

## might want to set tz in compose...
setTimeZone

# cd into app dir
if [ -d /home/hivekeeper/dash_app/ ]
  then
    echo "[ENTRYPOINT] changing to dir: /home/hivekeeper/dash_app"
    cd /home/hivekeeper/dash_app/

    # check if files exist and have content
    if [ -s hivekeepers_app.py ]
      then
        echo "[ENTRYPOINT] hivekeepers_app.py is populated!"

        if [ -s startup_update_db.py ]
          then
            echo "[ENTRYPOINT] found update db script file!"
            echo "[ENTRYPOINT] building database..."
            
            # build local db from remote source
            python3 startup_update_db.py
            
            if [ -s hivekeepers.db ]
              then
                echo "[ENTRYPOINT] database created!"
                
                # tail app logging
                echo "[ENTRYPOINT] setup tailing of app log"
                tail -n 0 -f /home/hivekeeper/gunicorn-logs/*.log &

                # start dash app via wsgi (gunicorn)
                echo "[ENTRYPOINT] starting application dashboard..."
                gunicorn3 hivekeepers_app:server \
                --bind 0.0.0.0:$port \
                --workers $workers \
                --worker-tmp-dir /dev/shm \
                --threads $threads \
                --log-level="$log_level" \
                --log-file=/home/hivekeeper/gunicorn-logs/gunicorn.log \
                --access-logfile=/home/hivekeeper/gunicorn-logs/access.log \
                "$@"
              else
                echo "[ENTRYPOINT] [ERROR] database missing!"
            fi
          else
            echo "[ENTRYPOINT] [ERROR] startup_update_db.py NOT found!"
        fi
      else
        echo "[ENTRYPOINT] [ERROR] hivekeepers_app.py is not unpopulated!"
    fi
  else
    echo "[ENTRYPOINT] [ERROR] /home/hivekeeper/dash_app not found!"
fi