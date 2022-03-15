#!/bin/bash

# HiveKeepers - container1 - docker-entrypoint.sh
# written by: Andrew McDonald
# initial: 26/01/22
# current: 15/03/22
# version: 0.9

set -e

echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] ----------- USER ID: " $(id hivekeeper) 

echo $(ls -l )
touch /home/hivekeeper/logs/container1-entrypoint.log

echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] === STARTING CONTAINER1 ===" | tee -a /home/hivekeeper/logs/container1-entrypoint.log

echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] ----------- USER ID: " $(id hivekeeper) | tee -a /home/hivekeeper/logs/container1-entrypoint.log

# get relevant environment variables, otherwise use defaults
log_level=${PROXY_LOG_LEVEL:-simple}
log_level_lower=${log_level,,}
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] user passed proxy logging level: " $log_level_lower | tee -a /home/hivekeeper/logs/container1-entrypoint.log

echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] ----------- USER ID: " $(id hivekeeper) | tee -a /home/hivekeeper/logs/container1-entrypoint.log

nginx_error_log=${NGINX_ERROR_LOG_LEVEL}
nginx_error_log_lower=${nginx_error_log,,}
echo 'date +"%Y-%m-%d %H:%M:%S" [CONTAINER1] user passed nginx error logging level: ' $nginx_error_log | tee -a /home/hivekeeper/logs/container1-entrypoint.log

app_proxy_port=${APP_PORT:-8050}
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] user passed app port: " $app_proxy_port | tee -a /home/hivekeeper/logs/container1-entrypoint.log

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

## set up nginx reverse proxy access
if [ -s /scripts/password_script.sh ]; then
    if [ -f /scripts/user_credentials.txt ]; then
        if [ -s /scripts/user_credentials.txt ]
          then
            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] found password script." | tee -a /home/hivekeeper/logs/container1-entrypoint.log
            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] found user credentials text file." | tee -a /home/hivekeeper/logs/container1-entrypoint.log
            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] user credentials text file is populated!" | tee -a /home/hivekeeper/logs/container1-entrypoint.log
            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] creating user credentials for proxy..." | tee -a /home/hivekeeper/logs/container1-entrypoint.log

            ## run user password create script
            /bin/bash /scripts/password_script.sh /scripts/user_credentials.txt

            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] deleting user credentials text file..." | tee -a /home/hivekeeper/logs/container1-entrypoint.log

            ## delete plain-text user passwords file
            rm /scripts/user_credentials.txt

            if [ ! -f user_credentials.txt ]
              then
                echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] user credentials text file deleted" | tee -a /home/hivekeeper/logs/container1-entrypoint.log
              else
                echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] [ERROR] user credentials text file not deleted!" | tee -a /home/hivekeeper/logs/container1-entrypoint.log
            fi
          else
            echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] user credentials text file is empty" | tee -a /home/hivekeeper/logs/container1-entrypoint.log
        fi
    fi
fi

# set password:username delimter, :
FS=":"

# log users with proxy access
while read line || [ -n "$line" ];
do
  # print user log access
  NAME=$(echo $line|cut -d$FS -f1)
  echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] ACCESS CREDENTIALS FOUND FOR USER: " $NAME | tee -a /home/hivekeeper/logs/container1-entrypoint.log
done < /etc/nginx/auth/.htpasswd

## run nginx env setup script
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] running nginx envsubstitution template script..." | tee -a /home/hivekeeper/logs/container1-entrypoint.log
/bin/bash /docker-entrypoint.d/20-envsubst-on-templates.sh

# make sure log files exist
touch /home/hivekeeper/logs/nginx-access.log
touch /home/hivekeeper/logs/nginx-error.log
touch /home/hivekeeper/logs/fail2ban.log

## setup fail2ban ip banning service
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] setting up fail2ban service..." | tee -a /home/hivekeeper/logs/container1-entrypoint.log
service fail2ban status > /dev/null && service fail2ban stop
rm -f /var/run/fail2ban/*

## start fail2ban
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] starting fail2ban service..." | tee -a /home/hivekeeper/logs/container1-entrypoint.log
sudo service fail2ban start #--chuid hivekeeper

## start nginx reverse proxy service
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] starting nginx proxy service..." | tee -a /home/hivekeeper/logs/container1-entrypoint.log
nginx

## start tail of service logs
echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] tailing nginx and fail2ban service logs..." | tee -a /home/hivekeeper/logs/container1-entrypoint.log
if [ "$log_level_lower" == "simple" ]
  then
    echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] setting service logs tail verbosity to: simple" | tee -a /home/hivekeeper/logs/container1-entrypoint.log
    exec tail -f /home/hivekeeper/logs/nginx-error.log /home/hivekeeper/logs/fail2ban.log
elif [ "$log_level_lower" == "detailed" ]
  then
    echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] setting service logs tail verbosity to: detailed" | tee -a /home/hivekeeper/logs/container1-entrypoint.log
    exec tail -f /home/hivekeeper/logs/nginx-access.log /home/hivekeeper/logs/nginx-error.log /home/hivekeeper/logs/fail2ban.log
else # set simple by default
  echo $(date +"%Y-%m-%d %H:%M:%S") "[CONTAINER1] setting service logs tail verbosity to default: simple" | tee -a /home/hivekeeper/logs/container1-entrypoint.log
  exec tail -f /home/hivekeeper/logs/nginx-error.log /home/hivekeeper/logs/fail2ban.log
fi

