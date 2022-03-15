#!/bin/bash

# HiveKeepers - container2 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 28/01/22
# current: 15/03/22
# version: 0.9

set -e

echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] ----------- USER ID: " $(id hivekeeper) 

# make sure log file exists
touch /home/hivekeeper/logs/container2-entrypoint.log

echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] === STARTING CONTAINER2 ===" | tee -a /home/hivekeeper/logs/container2-entrypoint.log

echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] ----------- USER ID: " $(id hivekeeper) | tee -a /home/hivekeeper/logs/container2-entrypoint.log

# get the CPU core count
cores=$(date +"%Y-%m-%d %H:%M:%S" "Threads/core: $(nproc --all)" | awk '{ print $2 }')
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] number of cores found: " $cores | tee -a /home/hivekeeper/logs/container2-entrypoint.log

# set Gunicorn number of workers - default to nummber of cores
workers="${APP_WORKERS:-$cores}"
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] setting gunicorn workers: " $workers | tee -a /home/hivekeeper/logs/container2-entrypoint.log

# set Gunicorn number of threads - default to number of cores - 1
threads_default=$(($cores - 1))
threads="${APP_THREADS:-$threads_default}"
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] setting gunicorn threads: " $threads | tee -a /home/hivekeeper/logs/container2-entrypoint.log

# get Gunicorn/Dash bind port
port="${APP_PORT:-8050}"
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] setting gunicorn listening port: " $port | tee -a /home/hivekeeper/logs/container2-entrypoint.log

# get App logging level
log_level=${APP_LOG_LEVEL:-info}
log_level_lower=${log_level,,}

echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] setting application logging level: " $log_level_lower | tee -a /home/hivekeeper/logs/container2-entrypoint.log

#threads=1 # setting single thread

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
    echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] changing to dir: /home/hivekeeper/dash_app" | tee -a /home/hivekeeper/logs/container2-entrypoint.log
    cd /home/hivekeeper/dash_app/

    # check if files exist and have content
    if [ -s hivekeepers_app.py ]
      then
        echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] hivekeepers_app.py is populated!" | tee -a /home/hivekeeper/logs/container2-entrypoint.log

        if [ -s startup_update_db.py ]
          then
            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] found update db script file!" | tee -a /home/hivekeeper/logs/container2-entrypoint.log
            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] building database..." | tee -a /home/hivekeeper/logs/container2-entrypoint.log

            # build local db from remote source
            python3 startup_update_db.py

            if [ -s hivekeepers.db ]
              then
                echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] database created!" | tee -a /home/hivekeeper/logs/container2-entrypoint.log
                
                # make sure log files exist
                touch /home/hivekeeper/logs/gunicorn.log
                touch /home/hivekeeper/logs/gunicorn-error.log
                touch /home/hivekeeper/logs/gunicorn-access.log

                # tail app logging
                echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] setup tailing of app log" | tee -a /home/hivekeeper/logs/container2-entrypoint.log
                tail -f /home/hivekeeper/logs/gunicorn.log &
                tail -f /home/hivekeeper/logs/gunicorn-error.log &
                tail -f /home/hivekeeper/logs/gunicorn-access.log &

                # start dash app via wsgi (gunicorn)
                echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] starting application dashboard..." | tee -a /home/hivekeeper/logs/container2-entrypoint.log
                gunicorn3 hivekeepers_app:server \
                --bind 0.0.0.0:$port \
                --workers $workers \
                --worker-tmp-dir /dev/shm \
                --threads $threads \
                --log-level=$log_level_lower \
                --access-logfile=- \
                --log-file=/home/hivekeeper/logs/gunicorn.log \
                --error-logfile=/home/hivekeeper/logs/gunicorn-error.log \
                --access-logfile=/home/hivekeeper/logs/gunicorn-access.log \
                #--log-file=- \
                #--error-logfile=- \
                "$@"
              else
                echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] [ERROR] database missing!" | tee -a /home/hivekeeper/logs/container2-entrypoint.log
            fi
          else
            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] [ERROR] startup_update_db.py NOT found!" | tee -a /home/hivekeeper/logs/container2-entrypoint.log
        fi
      else
        echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] [ERROR] hivekeepers_app.py is not unpopulated!" | tee -a /home/hivekeeper/logs/container2-entrypoint.log
    fi
  else
    echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER2] [ERROR] /home/hivekeeper/dash_app not found!" | tee -a /home/hivekeeper/logs/container2-entrypoint.log
fi
