#!/bin/sh

FS=":"
FILE=$1
while read line || [ -n "$line" ];
do
        # store field 1
        NAME=$(echo $line|cut -d$FS -f1)
        # store field 2
        PASSWORD=$(echo $line|cut -d$FS -f2)
        htpasswd -b /etc/nginx/auth/.htpasswd $NAME $PASSWORD
done < $FILE

exit