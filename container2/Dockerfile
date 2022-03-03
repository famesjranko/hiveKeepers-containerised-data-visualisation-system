# HiveKeepers - container1 - Dockerfile
# written by: Andrew McDonald
# initial: 28/01/22
# current: 04/02/22
# version: 0.4

FROM debian:stable-slim

LABEL maintainer="andrew mcdonald <17961040@students.ltu.edu.au>"

# installations and clean up 
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update -y && \
    apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    util-linux \
    sqlite3 \
    nano \
    && rm -rf /var/lib/apt/lists/*

# create app & logging directories
RUN mkdir -p /dash_app \
    && chmod 777 /dash_app

#RUN touch /dash_app/hivekeeper.db \
#    && chmod 777 /dash_app/hivekeeper.db

RUN mkdir -p /gunicorn-logs

# copy script and make executable
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# set app healthcheck
#HEALTHCHECK --interval=30s --timeout=3s \
#  CMD if [ $(curl -s -o /dev/null -w "%{http_code}" localhost/healthcheck) == 200 ]; then echo 0; else echo 1; fi

# run final init script
ENTRYPOINT ["/entrypoint.sh"]
