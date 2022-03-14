#!/bin/sh

# create access file if it deosn't exist
touch .htpasswd

# set password:username delimter, :
FS=":"

FILE=$1

while read line || [ -n "$line" ];
do
  # store field 1 - username
  NAME=$(echo $line|cut -d$FS -f1)

  # store field 2 - password
  PASSWORD=$(echo $line|cut -d$FS -f2)

  # add username and encrypted password to access file
  htpasswd -b .htpasswd $NAME $PASSWORD
done < $FILE
