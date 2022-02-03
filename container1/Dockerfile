# HiveKeepers - container1 - Dockerfile
# written by: Andrew McDonald
# initial: 26/01/22
# current: 30/01/22
# version: 0.1

FROM debian:stable-slim

LABEL maintainer="andrew mcdonald <17961040@students.ltu.edu.au>"

# installations and clean up 
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update -y && \
    apt-get install -y \
    fail2ban \
    iptables \
    exim4 \
    bsd-mailx \
    whois \
    nginx \
    apache2-utils \ 
    wget \
    util-linux \
    nano \
    && rm -rf /var/lib/apt/lists/*

# copy script and make executable
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# create log folder for sshd jail - prevents sshd jail log error
#RUN touch /var/log/auth.log

# create fail2ban local configurations
RUN cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
RUN cp /etc/fail2ban/fail2ban.conf /etc/fail2ban/fail2ban.local

# create dir for basic-auth file .htpasswd
RUN mkdir -p /etc/nginx/auth

# set nginx healthcheck
# nginx    -> done
# fail2ban -> ?
HEALTHCHECK --interval=30s --timeout=3s \
  CMD if [ $(curl -s -o /dev/null -w "%{http_code}" localhost/healthcheck) == 200 ]; then echo 0; else echo 1; fi

# run final init script
ENTRYPOINT ["/entrypoint.sh"]
