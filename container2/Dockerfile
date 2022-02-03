# HiveKeepers - container1 - Dockerfile
# written by: Andrew McDonald
# initial: 28/01/22
# current: 30/01/22
# version: 0.1

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
    util-linux \
    nano \
    apache2 \
    && rm -rf /var/lib/apt/lists/*

# update pip
RUN python3 -m pip install --upgrade pip setuptools

# create app directory
RUN mkdir -p /hivekeepers/dash_app

# copy script and make executable
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# set app healthcheck
#HEALTHCHECK --interval=30s --timeout=3s \
#  CMD if [ $(curl -s -o /dev/null -w "%{http_code}" localhost/healthcheck) == 200 ]; then echo 0; else echo 1; fi

# run final init script
ENTRYPOINT ["/entrypoint.sh"]
