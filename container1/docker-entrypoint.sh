# HiveKeepers - container1 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 26/01/22
# current: 30/01/22
# version: 0.4

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

## setup fail2ban
service fail2ban status > /dev/null && service fail2ban stop
rm -f /var/run/fail2ban/*
service fail2ban start

## run nginx and tail log
nginx
tail -f /var/log/nginx/access.log
