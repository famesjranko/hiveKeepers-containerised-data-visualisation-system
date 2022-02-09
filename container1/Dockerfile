# HiveKeepers - container1 - Dockerfile
# written by: Andrew McDonald
# initial: 26/01/22
# current: 04/02/22
# version: 0.1

#FROM debian:stable-slim
FROM nginx:1.20.2

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
    apache2-utils \
    wget \
    util-linux \
    nano \
    && rm -rf /var/lib/apt/lists/*

# copy script and make executable
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# copy fail2ban local/docker configurations
WORKDIR /etc/fail2ban
COPY ./fail2ban/jail.local .
COPY ./fail2ban/fail2ban.local .
COPY ./fail2ban/action.d/docker-iptables-multiport.conf ./action.d
COPY ./fail2ban/filter.d/nginx-http-auth.conf ./filter.d
COPY ./fail2ban/jail.d/nginx.conf ./jail.d

# create log folder for sshd jail - prevents sshd jail log error
RUN touch /var/log/auth.log

# copy nginx configurations
WORKDIR /etc/nginx
COPY ./nginx/nginx.conf .

# copy fixed nginx-docker ENV substition template script
COPY fixed_envsubst-on-templates.sh /docker-entrypoint.d/20-envsubst-on-templates.sh
RUN chmod +x /docker-entrypoint.d/20-envsubst-on-templates.sh

# setup nginx logging for fail2ban access
RUN mkdir /nginx-logs
RUN touch /nginx-logs/error.log
RUN touch /nginx-logs/access.log

# add HiveKeepers root web page
WORKDIR /var/www/html
COPY ./nginx/html/index.html .
COPY ./nginx/html/background.jpg .

# create dir for basic-auth file .htpasswd
RUN mkdir -p /etc/nginx/auth

# set nginx healthcheck
# nginx    -> done
# fail2ban -> ?
HEALTHCHECK --interval=30s --timeout=3s \
  CMD if [ $(curl -s -o /dev/null -w "%{http_code}" localhost/healthcheck) == 200 ]; then echo 0; else echo 1; fi

# run final init script
ENTRYPOINT ["/entrypoint.sh"]
