#!/bin/bash

# HiveKeepers - container1 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 26/01/22
# current: 04/02/22
# version: 0.7

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
echo "[ENTRYPOINT] setting system time..."
setTimeZone

## setup fail2ban
echo "[ENTRYPOINT] setting up fail2ban server and starting..."
service fail2ban status > /dev/null && service fail2ban stop
rm -f /var/run/fail2ban/*
service fail2ban start

## run nginx and tail log
echo "[ENTRYPOINT] starting nginx and tailing log..."
nginx
exec tail -f /var/log/nginx/access.log
