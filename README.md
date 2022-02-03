# HiveKeepers Internship Project
La Trobe University and HiveKeepers internship project

## Outline of project directories:

### Container1: nginx and fail2ban

```bash
container1/
├── auth/
│   └── .htpasswd
├── docker-entrypoint.sh
├── Dockerfile
├── fail2ban
│   ├── action.d/
│   │   └── docker-iptables-multiport.conf
│   ├── fail2ban.conf
│   ├── fail2ban.d/
│   ├── fail2ban.local
│   ├── filter.d/
│   │   └── nginx-http-auth.conf
│   ├── jail.conf
│   ├── jail.d/
│   │   ├── defaults-debian.conf
│   │   └── nginx.conf
│   ├── jail.local
│   ├── paths-arch.conf
│   ├── paths-common.conf
│   ├── paths-debian.conf
│   └── paths-opensuse.conf
├── nginx/
│   ├── default
│   └── nginx.conf
└── readme
```

### Continer2: python Dash

```bash
container2/
├── dash-app/
│   ├── hivekeepers_app.py
│   ├── requirements.txt
│   └── sync_data_202201231041.csv
├── docker-entrypoint.sh
└── Dockerfile
```

## Getting started
First, clone the repositoriy to local machine and cd into project directory. 

Then create a user and encrypted password for nginx access.  Simplest way to do this is to use apache2-utils (Debian, Ubuntu) or httpd-tools (RHEL/CentOS/Oracle Linux) for this purpose.

Debian example: in the project directory, run:
```bash
sudo htpasswd /container1/auth/.htpasswd username
```
To create more than 1 user, simply run the command again for a new username.

Once user:password created, run "docker-compose up" or "docker-compose up -d" to run daemonised.

WEB ACCESS: http://localhost/app/
