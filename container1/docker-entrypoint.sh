#!/bin/bash

# HiveKeepers - container1 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 26/01/22
# current: 04/02/22
# version: 0.7

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
echo "[ENTRYPOINT] setting system time..."
setTimeZone

## set up nginx reverse proxy access
if [ -s /scripts/password_script.sh ]
  then
    echo "[ENTRYPOINT] found password script."

    if [ -f /scripts/user_credentials.txt ]
      then
        echo "[ENTRYPOINT] found user credentials text file."
    
        if [ -s /scripts/user_credentials.txt ]
          then
            echo "[ENTRYPOINT] user credentials text file is populated!"
            echo "[ENTRYPOINT] creating user credentials for proxy..."

            ## run user password create script
            /bin/bash /scripts/password_script.sh /scripts/user_credentials.txt

            echo "[ENTRYPOINT] deleting user credentials text file..."

            ## delete plain-text user passwords file
            rm /scripts/user_credentials.txt

            if [ ! -f user_credentials.txt ]
              then
                echo "[ENTRYPOINT] user credentials text file deleted"
              else
                echo "[ENTRYPOINT] [EEOR] user credentials text file not deleted!"
            fi
          else
            echo "[ENTRYPOINT] user credentials text file is empty"
        fi
    fi
fi

## setup fail2ban ip banning service
echo "[ENTRYPOINT] setting up fail2ban service..."
service fail2ban status > /dev/null && service fail2ban stop
rm -f /var/run/fail2ban/* 

## start fail2ban
echo "[ENTRYPOINT] starting fail2ban service..."
sudo service fail2ban start #--chuid hivekeeper

## run nginx env setup script
echo "[ENTRYPOINT] running nginx envsubstitution template script..."
/bin/bash /docker-entrypoint.d/20-envsubst-on-templates.sh

## start nginx reverse proxy service
echo "[ENTRYPOINT] starting nginx proxy service..."
nginx

## start tail of service logs
echo "[ENTRYPOINT] tailing nginx and fail2ban service logs..."
exec tail -f /nginx-logs/access.log nginx-logs/error.log /var/log/fail2ban.log
