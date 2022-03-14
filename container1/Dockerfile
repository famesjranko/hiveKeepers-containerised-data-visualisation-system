# HiveKeepers - container1 - Dockerfile
# written by: Andrew McDonald
# initial: 26/01/22
# current: 25/02/22
# version: 0.3

#FROM debian:stable-slim
FROM nginx:1.20.2

# set container maintainer
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
    sudo \
    && rm -rf /var/lib/apt/lists/*

# create non-root user
# have to use NOPASSWD:ALL for fail2ban to run.
# But may be posible to limit this to a specific bin file if fail2ban process tree understood better
RUN addgroup --system hivekeeper && adduser --system --group hivekeeper && \
    usermod -a -G adm hivekeeper && \
    usermod -a -G sudo hivekeeper && \
    echo "hivekeeper ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/99_sudo_include_file

# copy nginx configurations
WORKDIR /etc/nginx
COPY ./nginx/nginx.conf .
COPY ./nginx/templates templates/

# copy nginx env substitution script
COPY fixed_envsubst-on-templates.sh /docker-entrypoint.d/20-envsubst-on-templates.sh

# create dir for basic-auth file .htpasswd and set user access
RUN mkdir -p auth && \
    touch auth/.htpasswd && \
    chown -R hivekeeper:hivekeeper auth/.htpasswd

# add basic hivekeeper root web page
WORKDIR /var/www/html
COPY ./nginx/html/index.html .
COPY ./nginx/html/background.jpg .

# setup nginx logging for fail2ban access
WORKDIR /
RUN mkdir -p nginx-logs && \
    touch nginx-logs/error.log && \
    touch nginx-logs/access.log

# set user permissions and executables for nginx
RUN touch /run/nginx.pid && \
    chown -R hivekeeper:hivekeeper /run/nginx.pid && \
    chown -R hivekeeper:hivekeeper /etc/nginx && \
    chown -R hivekeeper:hivekeeper /var/www/html && \
    chown -R hivekeeper:hivekeeper /nginx-logs && \
    chown -R hivekeeper:hivekeeper /var/cache/nginx && \
    chown -R hivekeeper:hivekeeper /etc/logrotate.d && \
    chmod +x /docker-entrypoint.d/20-envsubst-on-templates.sh && \
    chown -R hivekeeper:hivekeeper /docker-entrypoint.d

# copy fail2ban local/docker configurations
WORKDIR /etc/fail2ban
COPY ./fail2ban/jail.local .
COPY ./fail2ban/fail2ban.local .
COPY ./fail2ban/action.d/docker-iptables-multiport.conf ./action.d
COPY ./fail2ban/filter.d/nginx-http-auth.conf ./filter.d
COPY ./fail2ban/jail.d/nginx.conf ./jail.d

# create log folder for sshd jail - prevents sshd jail log error
RUN touch /var/log/auth.log 

# set user permissions and executables for fail2ban
RUN touch /var/log/auth.log && \
    chown -R hivekeeper:hivekeeper /var/log/auth.log && \
    chown -R hivekeeper:hivekeeper /etc/fail2ban && \
    chown -R hivekeeper:hivekeeper /var/log && \
    mkdir -p /var/run/fail2ban && \
    touch /var/run/fail2ban/fail2ban.pid && \
    chown -R hivekeeper:hivekeeper /var/run/fail2ban/fail2ban.pid && \
    chown -R hivekeeper:hivekeeper /var/run/fail2ban && \
    chown -R hivekeeper:hivekeeper /etc/init.d/fail2ban && \
    chown -R hivekeeper:hivekeeper /var/lib/fail2ban/

# copy fixed nginx-docker ENV substition template script
RUN mkdir -p /scripts
WORKDIR /scripts

# copy password script
COPY password_script.sh .

# copy user credentials file for access
# make and store this file within container1/ if you want to bake in user password
# access into the base image created by this Dockerfile.
# text file structure is: user:password (per line)
#   eg:
#       user1:password1
#       user2:password2
#       user3:password3
#       ...
# NOTE: cannot be used if passing .htpasswd file in via docker-compose.yaml file

#COPY user_credentials.txt .

# set permissions for scripts
RUN chmod +x password_script.sh && \
    chown -R hivekeeper:hivekeeper /scripts

# change back to root /
WORKDIR /

# service healthchecks
# nginx    -> done
# fail2ban -> done
COPY healthcheck.sh .

# copy init script
COPY docker-entrypoint.sh entrypoint.sh

# set permissions and make executable
RUN chmod +x healthcheck.sh && \
    chown hivekeeper:hivekeeper healthcheck.sh && \
    chmod +x entrypoint.sh && \
    chown hivekeeper:hivekeeper entrypoint.sh

# change to non-root user
USER hivekeeper

# run healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s \  
    CMD /healthcheck.sh

# run final init script
ENTRYPOINT ["/entrypoint.sh"]