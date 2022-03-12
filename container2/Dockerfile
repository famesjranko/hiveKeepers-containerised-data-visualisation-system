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
    python3 \
    python3-pip \
    sqlite3 \
	python3-pymysql \
    gunicorn3 \
    nano \
    && rm -rf /var/lib/apt/lists/*

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

RUN touch /home/hivekeeper/gunicorn-logs/access.log && \
    touch /home/hivekeeper/gunicorn-logs/gunicorn.log

# copy Dash application folder
COPY dash_app /home/hivekeeper/dash_app

# update user app file permissions for user
RUN touch /home/hivekeeper/dash_app/hivekeepers.db && \
    chown -R hivekeeper:hivekeeper /home/hivekeeper

# add local user bin to PATH
RUN PATH="'/home/hivekeeper/.local/bin:$PATH"

# change to non-root user
USER hivekeeper

# set working directory
WORKDIR /home/hivekeeper/dash_app

# update pip,etc and install python app requirements
RUN python3 -m pip install --upgrade pip setuptools wheel --no-warn-script-location && \
    pip3 install -r requirements.txt --no-warn-script-location

# set app healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s \  
    CMD /healthcheck.sh

# run final init script
ENTRYPOINT ["/entrypoint.sh"]
