# HiveKeepers - container2 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 28/01/22
# current: 30/01/22
# version: 0.1

#!/bin/bash

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
    echo "requirements.txt is populated; running pip..."

    # install dash app requirements
    pip3 install -r requirements.txt

    # start dash app
    python3 ./hivekeepers_app.py
  else
    echo "requirements.txt is empty; not running pip."
fi
