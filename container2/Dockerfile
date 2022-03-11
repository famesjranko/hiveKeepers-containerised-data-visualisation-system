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
	python3-pymysql \
    nano \
    && rm -rf /var/lib/apt/lists/*

# create default group and user
RUN groupadd -g 1000 hivekeeper
RUN useradd --create-home --gid 1000 --uid 1000 --shell /bin/bash hivekeeper

# set the default user
USER hivekeeper

# set working directory
WORKDIR /home/hivekeeper

# create app & logging directories
RUN mkdir -p /home/hivekeeper/dash_app
RUN mkdir -p /home/hivekeeper/gunicorn-logs

# copy Dash application folder
COPY dash_app /home/hivekeeper/dash_app

# change user to root 
USER root

# copy script and make executable
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# copy service healthcheck
# dash    -> done
COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# change back to default user
USER hivekeeper

# copy Dash application folder
COPY ./dash_app /dash_app

# set app healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s \  
    CMD /healthcheck.sh

# run final init script
ENTRYPOINT ["/entrypoint.sh"]
