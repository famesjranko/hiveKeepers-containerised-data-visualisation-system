# HiveKeepers - container2 - Dockerfile
# written by: Andrew McDonald
# initial: 28/01/22
# current: 17/03/22
# version: 0.9

# get base image
FROM debian:stable-slim

# set container maintainer
LABEL maintainer="andrew mcdonald <17961040@students.ltu.edu.au>"

# installations and clean up 
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update -y && \
    apt-get install -y \
    python3 \
    python3-pip \
    sqlite3 \
    python3-pymysql \
    gunicorn3 \
    procps \
    monit \
    curl \
    lsof \
    && rm -rf /var/lib/apt/lists/*

# set working directory
WORKDIR /

# copy script and make executable
COPY docker-entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh

# copy service healthcheck
# dash    -> done
COPY healthcheck.sh healthcheck.sh
RUN chmod +x healthcheck.sh

# create logging directory
RUN mkdir -p /home/hivekeeper/logs

WORKDIR /etc/monit
COPY ./monit/monitrc .
RUN chmod 700 monitrc
COPY ./monit/gunicorn3.conf conf.d/gunicorn3.conf

# set working directory
WORKDIR /home/hivekeeper

# copy Dash application folder
COPY dash_app /home/hivekeeper/dash_app

# update user app file permissions for user
RUN chmod -R 664 /home/hivekeeper/

# set working directory
WORKDIR /home/hivekeeper/dash_app

# update pip,etc and install python app requirements
RUN python3 -m pip install --upgrade pip setuptools wheel --no-warn-script-location && \
    pip3 install -r requirements.txt --no-warn-script-location

# set app healthcheck
HEALTHCHECK --interval=120s --timeout=10s --start-period=60s \  
    CMD /healthcheck.sh

# run final init script
ENTRYPOINT ["/entrypoint.sh"]
