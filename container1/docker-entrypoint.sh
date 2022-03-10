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

## check if files exist and have content
if [ -s "/password_script.sh" ]; then

    if [ -s "user_passwords.txt" ]; then
    echo "[ENTRYPOINT] creating user credentials for proxy..."

    ## run user password create script
    /bin/bash /password_script.sh user_passwords.txt

    echo "[ENTRYPOINT] deleting user password file..."

    ## delete plain-text user passwords file
    rm user_passwords.txt
    fi
fi

## setup fail2ban
echo "[ENTRYPOINT] setting up fail2ban server and starting..."
service fail2ban status > /dev/null && service fail2ban stop
rm -f /var/run/fail2ban/*
service fail2ban start

echo "[ENTRYPOINT] running nginx envsubstitution template script..."
/bin/bash /docker-entrypoint.d/20-envsubst-on-templates.sh

## run nginx and tail log
echo "[ENTRYPOINT] starting nginx..."
nginx

# delete user plain text passwords when script finished
echo "[ENTRYPOINT] deleting user password file..."
rm user_passwords.txt

echo "[ENTRYPOINT] tailing nginx and fail2ban logs..."
exec tail -f /nginx-logs/access.log /var/log/fail2ban.log
