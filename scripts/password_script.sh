#!/bin/sh

# HiveKeepers - scripts - password_script.sh
# written by: Andrew McDonald
# initial: 28/01/22
# current: 15/03/22
# version: 0.9

## ===================================================
## script creates an encrypted user access file for
## use with nginx basic-auth.
## 
## requires: htpasswd
##
## to use: 
##   create a text file with a user:password text pair
##   per user, per line.   Then call script with text
##   file as argument.
##     eg: ./password_script user_credentials.txt
##
## eg txt file layout for creating 3 users:
##
##   user_credentials.txt:
##   user1:password1
##   user2:password2
##   user3:password3
## ===================================================

# create access file if it deosn't exist
touch .htpasswd

# set password:username delimter, :
FS=":"

FILE=$1

# empty file contents...
echo "" > $FILE

while read line || [ -n "$line" ];
do
  # store field 1 - username
  NAME=$(echo $line|cut -d$FS -f1)

  # store field 2 - password
  PASSWORD=$(echo $line|cut -d$FS -f2)

  # add username and encrypted password to access file
  htpasswd -b .htpasswd $NAME $PASSWORD
done < $FILE
