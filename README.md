# HiveKeepers Internship Project
La Trobe University and HiveKeepers internship project

---

### Outline of project:
Build and present a containerised website for presenting apiary data from remote MySQL server, with user authentication and IP banning services.
  
The system comprises of two distinct Docker containers, running on their own private container network.  Each container is given a static IP address for reliable inter-container communication and referencing.  

---

**directory structure**  
```bash
project
├── container1
│   ├── docker-entrypoint.sh
│   ├── Dockerfile
│   ├── fail2ban
│   │   ├── action.d
│   │   │   └── docker-iptables-multiport.conf
│   │   ├── fail2ban.local
│   │   ├── filter.d
│   │   │   └── nginx-http-auth.conf
│   │   ├── jail.d
│   │   │   └── nginx.conf
│   │   └── jail.local
│   ├── fixed_envsubst-on-templates.sh
│   ├── healthcheck.sh
│   ├── monit
│   │   ├── fail2ban.conf
│   │   ├── monitrc
│   │   └── nginx.conf
│   ├── nginx
│   │   ├── default.old
│   │   ├── html
│   │   │   ├── background.jpg
│   │   │   └── index.html
│   │   ├── nginx.conf
│   │   └── templates
│   │       └── default.conf.template
│   └── password_script.sh
├── container2
│   ├── dash_app
│   │   ├── gunicorn_config.py
│   │   ├── hivekeepers_app.py
│   │   ├── hivekeepers_config.py
│   │   ├── hivekeepers_helpers.py
│   │   ├── requirements.txt
│   │   ├── start_app.sh
│   │   ├── startup_update_db.py
│   │   └── update_db.py
│   ├── docker-entrypoint.sh
│   ├── Dockerfile
│   ├── healthcheck.sh
│   └── monit
│       ├── gunicorn3.conf
│       └── monitrc
├── docker-compose.yml
├── htpasswd
├── README.md
└── scripts
    ├── password_script.sh
    └── user_credentials.txt
```

---

### System Info
**names:**  
container1: reverse-proxy  
container2: dash-app  
  
**services:**  
container1: nginx, fail2ban, monit   
container2: Dash (Python), Gunicorn, monit   
  
**container network:**  
subnet: 172.75.0.0/16   
container1 ip: 172.75.0.2   
container2 ip: 172.75.0.3   

**Default Visualisation App Access (through proxy; can be changed/removed):**  
Username: hivekeepers  
Password: hivekeepers  

---

**Software Versions**  
container1:
  
| service            | source                        | version       |
| ------------------ | ----------------------------- | ------------- |
| Docker base Image  | Docker Hub (NGINX official)   | nginx:1.20.2  |
| NGINX              | Baked into base image         | 1.20.2        |
| Fail2ban           | Debian repository             | 0.11.2        |
| Monit              | Debian repository             | 5.27.2        |
  
container2:
  
| service            | source                        | version             |
| ------------------ | ----------------------------- | ------------------- |
| Docker base Image  | Docker Hub (Debian official)  | debian:stable-slim  |
| Pyython            | Debian repository             | 3.9.2               |
| SQLite             | Debian repository             | 3.34.1              |
| Gunicorn3          | Debian repository             | 20.1.0              |
| Monit              | Debian repository             | 5.27.2              |

---

**Environment Variables:**  
container1:

|                          |        |                                                                                             |
| ------------------------ | ------ | ------------------------------------------------------------------------------------------- |
| APP_PORT                 | INT    | Port to proxy to on container2, must match in both containers (defaults to 8050 if not set) |
| PROXY_LOG_LEVEL          | STRING | options: simple (no nginx access logging), detailed (with nginx access logging)             |
| NGINX_ERROR_LOG_LEVEL    | STRING | options: info, notice, warn, error, crit, alert, emerg (case sensitive)                     |

container2:

|                          |        |                                                                                                   |
| ------------------------ | ------ | ------------------------------------------------------------------------------------------------- |
| MYSQL_USER               | STRING | username for remote MySQL DB                                                                      |
| MYSQL_PASS               | STRING | password or remote MySQL DB                                                                       |
| MYSQL_HOST               | STRING | URL for remote MySQL DB                                                                           |
| MYSQL_DB                 | STRING | database name of remote MySQL DB                                                                  |
| APP_WORKERS              | INT    | Gunicorn workers - defaults to number of cores                                                    |
| APP_THREADS              | INT    | Gunicorn threads - defaults to number of cores – 1                                                |
| APP_PORT                 | INT    | listening port for Gunicorn WSGI, must match in both containers (defaults to 8050 if not set)     |
| APP_LOG_LEVEL            | STRING | options: debug, info, warning, error, critical                                                    |
| START_TYPE               | STRING | options: Warm_Start, Cold_Start, Init_start (case sensitive) (defaults to  Warm_Start if not set) |

---

**Watchdog Services:**  
Container1:  
Monitoring software: Monit  
Monitored services: NGINX, Fail2ban  
Web-monitor portal: Yes  
  
Monit is set up to monitor NGINX and Fail2ban services every 2mins and reports the status of each and handles service restart duties if they are found to be inactive.  Nginx is monitored via PID file and /healthcheck on port 80 Nginx that returns http code 200 on success; Fail2ban is monitored via PID file and socket.
  
Monit also provides a web port to both monitor and control system services.  This portal is located on port 2812 of container1, and access is provided via NGINX reverse proxy features.  
  
  To access Monit’s web portal, visit http://[host-IP]/monit  
      credentials:  
          username: admin  
          password: hivekeeper  
 
Container2:  
Monitoring software: Monit  
Monitored services: NGINX, Fail2ban  
Web-monitor portal: No  
  
Monit is set up to monitor the Guniicorn service every 2mins and reports the status and handles service restart duties if they are found to be inactive.  Gunicorn is monitored via PID file and /ping on port 80 - /ping located in hivekeepers_app.py, which returns string: 'status: ok'  
  
**Command line access to watchdogs:**  
It is also possible to access and control watchdog states and status via the command line using: docker exec CONTAINER-NAME COMMAND ARGS
  
```bash
== available monit commands ==  
monit start all             			# Start all services  
monit start <name>          			# Only start the named service  
monit stop all              			# Stop all services  
monit stop <name>           			# Stop the named service  
monit restart all           			# Stop and start all services  
monit restart <name>        			# Only restart the named service  
monit monitor all           			# Enable monitoring of all services  
monit monitor <name>        			# Only enable monitoring of the named service  
monit unmonitor all         			# Disable monitoring of all services  
monit unmonitor <name>      			# Only disable monitoring of the named service  
monit reload                			# Reinitialize monit  
monit status [name]         			# Print full status information for service(s)  
monit summary [name]        			# Print short status information for service(s)  
monit report [up|down|..]   			# Report state of services. See manual for options  
monit quit                  			# Kill the monit daemon process  
monit validate              			# Check all services and start if not running  
monit procmatch <pattern>   			# Test process matching pattern  
```

---

### Container Info
**Container1**
Container1 handles all incoming network requests to the container network, and proxies any permissible requests destined for container2 to its respective static IP address.  
  
To handle incoming requests, container1 runs the NGINX service on port 80.  To control access to the container network, NGINX has basic-auth turned on and references a user:password file (.htpasswd) to determine relevant access privileges.  I Have made it so the password file can be created outside of the container and either passed in via the Dockerfile, or shared via a --volume -v in docker-compose.yaml
  
To handle requests that fail NGINX basic-auth 5 times, container1 also runs the service Fail2ban.  Fail2ban monitors the NGINX error log and records the IP address of failed access attempts to its log for future reference.  Once an IP address has reached 5 failed attempts within a given time span (10 mins) the IP address is banned from future access for 10 minutes – the number of attempts. the time frame for attempts, and the ban time can all be configured within Fail2bans configuration file before container1 build time if desired.  See authentification section for further explanation.  
    
To get fail2ban to work with iptables requires container privilege capabilities to be used:  
```bash
cap_add:
  - CAP_NET_ADMIN
  - CAP_NET_RAW
```
  
Nginx only using port 80 currently - atm don't see any need for SSL, but that might change...  
  
Monit is used as the watchdog handler for monitoring the NGINX and Fail2ban services and restarts if either are found to be down/unresponsive.  
  
**Container2**  
Container2 runs the HiveKeepers data visualisation web application, which displays 2d and 3d charts from timeseries data collected from apiaries. The application is written in Python and relies heavily on the Plotly Dash visualisation library.  The Web Server Gateway Interface (WSGI) Gunicorn is used to handle all web requests to and from the application, and data for visualising is pulled from the HiveKeepers remote MySQL database and stored locally in an SQLite database.  
  
Contiainer2 has no exposed ports and is only accessible from outside the container network via the container1 reverse proxy.  
  
---


---

### User Authentication
NGINX basic authentication user access is managed through a txt file container user:password combinations for referencing requests against.  This file needs to be passed/shared with container1.  And while it is possible to simply pass such a file in plain text, it is much safer to first encrypt the passwords listed before doing so…  
  
The simplest way to make such an encrypted user:password file is to use the apache2-utils library on Linux – the following is for Debian systems but can be modified for others.  
  
To get the library installed, run: ‘apt-get update && apt-get install apache2-utils -y’  
Then run as root, run: ‘htpasswd -c .htpasswd username’  
This will start the application, create the file, then ask you to input the password.  
  
To add more users, simply rerun the command, but use the -b flag in place of the -c flag.  
  
Or, if you have many users you wish to add, I have included a small BASH script (password_script.sh) that can automate the process by reading a plain text user:password structured file and converting it to an encrypted password version using apache2-utils.  
  
This script is located within the /script directory within the main project directory.  
to use, create a text file with a user:password text pair per user, per line.   Then call script with the text file as the first argument. e.g.: ‘ ./password_script user_credentials.txt’  
  
e.g., user_credentials.txt file layout for creating 3 users:  
```bash
user1:password1
user2:password2
user3:password3
```
  
### Getting started
First, clone the repositoriy to local machine and cd into project directory. 

Then create a user and encrypted password for nginx access.   
   
Simplest way to do this is to use apache2-utils (Debian, Ubuntu) or httpd-tools (RHEL/CentOS/Oracle Linux) for this purpose.

Debian example: in the project directory, run (-c to create file):
```bash
sudo htpasswd -c container1/auth/.htpasswd username
```
To create more than 1 user, simply run the command again with -b flag instead of -c   

Or use the password_script.sh file to automatically make the password file from a text file of user:passwords   
to use, create a text file with one user:password text pair per line:   
for example:   
```bash
user1:password1
user2:password2
user3:password3
```

to run script, simply pass the text file in as argument when running:   
```bash
./password_script.sh user_pass.txt
```

Once finished, a hidden file with encrypted user:password file is created in the cwd:   
```bash
.htpasswd
```

Once user:password created, run docker compose in base directory (-d to daemonise):
```bash
docker-compose up 
```

Once both containers have initialised, web access via http://localhost/app/

### default user
```bash
username: hivekeepers   
password: hivekeepers
```
container1 system diagram:  
![container1](readme-assets/container1-diagram-git.png)  
  
container2 system diagram:  
![container1](readme-assets/container2-diagram-git.png)  
  
container1 monit web portal for manager:  
![monit-web-portal](readme-assets/monit-web.png)  

container1 monit web portal for service (eg. ngix):
![monit-web-portal-service](readme-assets/monit-nginx-web.png)  
