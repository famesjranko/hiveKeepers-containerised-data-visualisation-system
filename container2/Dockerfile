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
#RUN groupadd -g 1000 hivekeeper
#RUN useradd --create-home --gid 1000 --uid 1000 --shell /bin/bash hivekeeper

# create non-root user
RUN addgroup --system hivekeeper && adduser --system --group hivekeeper

# set working directory
WORKDIR /

# copy script and make executable
COPY docker-entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh && \
    chown hivekeeper:hivekeeper entrypoint.sh

# copy service healthcheck
# dash    -> done
COPY healthcheck.sh healthcheck.sh
RUN chmod +x healthcheck.sh && \
    chown hivekeeper:hivekeeper healthcheck.sh

# set working directory
WORKDIR /home/hivekeeper

# create app & logging directories
RUN mkdir -p /home/hivekeeper/dash_app && \
    mkdir -p /home/hivekeeper/gunicorn-logs

# copy Dash application folder
COPY dash_app /home/hivekeeper/dash_app

# update user app file permissions for user
RUN touch /home/hivekeeper/dash_app/hivekeepers.db && \
    chown -R hivekeeper:hivekeeper /home/hivekeeper

# change to non-root user
USER hivekeeper

# set app healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s \  
    CMD /healthcheck.sh

# run final init script
ENTRYPOINT ["/entrypoint.sh"]
