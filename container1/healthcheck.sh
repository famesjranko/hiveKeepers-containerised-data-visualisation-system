#!/bin/bash

# HiveKeepers - container1 - healthycheck.sh
# written by: Andrew McDonald
# initial: 25/02/22
# current: 25/02/22
# version: 0.1

# this script runs simple health checks on
# nginx and fail2ban container services.
# returns 0 if healthy, 1 if unhealthy

# init service status variables
NGINX_STATUS=-1
FAIL2BAN_STATUS=-1

# check nginx status and update status var
if [ $(curl -s -o /dev/null -w "%{http_code}" localhost/healthcheck) == 200 ]
  then
    NGINX_STATUS=0
  else
    NGINX_STATUS=1
fi

# check fail2ban status and update status var
if [[ $(fail2ban-client ping) == "Server replied: pong" ]]
  then
    FAIL2BAN_STATUS=0
  else
    FAIL2BAN_STATUS=1
fi

# check status vars and return docker health status
if [[ $NGINX_STATUS == 0 && $FAIL2BAN_STATUS == 0 ]]
  then
    echo 0
  else
    echo 1
fi
