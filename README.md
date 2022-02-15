# HiveKeepers Internship Project
La Trobe University and HiveKeepers internship project

## Outline of project:

## Outline of containers:

#### services:
container1: nginx, fail2ban   
container2: python Dash, Gunicorn   

#### container network:
subnet: 172.75.0.0/16   
container1 ip: 172.75.0.2   
container2 ip: 172.75.0.3   

#### directory structure
```bash
├── container1
│   ├── auth
│   │   └── .htpasswd
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
│   ├── nginx
│   │   ├── auth
│   │   ├── default
│   │   ├── html
│   │   │   ├── background.jpg
│   │   │   └── index.html
│   │   └── nginx.conf
│   └── readme
├── container2
│   ├── dash_app
│   │   ├── gunicorn-logs
│   │   ├── hivekeepers_app.py
│   │   ├── requirements.txt
│   │   └── sync_data_202201231041.csv
│   ├── docker-entrypoint.sh
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

### Container1: nginx and fail2ban

So far, have nginx running as simple webserver/reverse-proxy with fail2ban banning IPs that fail nginx basic-auth.
Nginx's basic-auth file .htpasswd is stored locally in dir container1/auth/.  Have made it so the password file can
be created outside of container and either passed in via the Dockerfile, or shared via --volume -v in docker-compose.yaml

Nginx's proxy redirection to dash implemented in file nginx/default.

Nginx also has a basic health check location /healthcheck that returns http code 200 on success.
This is implemented as a basic container HEALTHCHECK within the Dockerfile

To get fail2ban to work with iptables requires container privilege capabilities to be used:
```bash
cap_add:
  - CAP_NET_ADMIN
  - CAP_NET_RAW
```

Nginx only using port 80 currently - atm don't see any need for SSL, but that might change...

### Continer2: python Dash

## Getting started
First, clone the repositoriy to local machine and cd into project directory. 

Then create a user and encrypted password for nginx access.   
   
Simplest way to do this is to use apache2-utils (Debian, Ubuntu) or httpd-tools (RHEL/CentOS/Oracle Linux) for this purpose.

Debian example: in the project directory, run (-c to create file):
```bash
sudo htpasswd -c container1/auth/.htpasswd username
```
To create more than 1 user, simply run the command again for a new username.

Once user:password created, run docker compose in base directory (-d to daemonise):
```bash
docker-compose up 
```

Once both containers have initialised, web access via http://localhost/app/
