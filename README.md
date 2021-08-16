# After the General Meeting

After the General Meeting some accounts and data needs to updated.
We generally add the new board members as soon as possible,
but only remove the old board members after the first board meeting.

## Before the first board meeting (as soon as possible)

- Update the board member page: https://fredagscafeen.dk/board/ (`docker exec -it web_app_1 ./manage.py new_board`)
- Add new board members and alternates to the best mailinglist: https://maillist.au.dk/mailman/admin/datcafe-best.cs/members/add
- Add new board members and alternates to the gitlab group with "Developer" role: https://gitlab.au.dk/groups/fredagscafeen/-/group_members
- Add new board members to the github organization with "Owner" role: https://github.com/orgs/fredagscafeen/people

## After the first board meeting

- Update https://fredagscafeen.dk/board/ with custom titles and images
- Remove old board members and alternates from the best mailinglist: https://maillist.au.dk/mailman/admin/datcafe-best.cs/members/list
- Remove old board members and alternates from the gitlab group: https://gitlab.au.dk/groups/fredagscafeen/-/group_members
- Remove old board members from the github organization: https://github.com/orgs/fredagscafeen/people
- Remove admin accounts for old board members and create admin accounts for new board members: `docker exec -it web_app_1 ./manage.py update_board_member_accounts`
- Change all passwords and update `.env` config: http://fredagscafeen.dk/admin/admin/logentry/secrets_view

### New web responsible

This only needs to be done, if there is a new web responsible:

- Make the new responsible's user a superuser on the website
- Add new keys to and remove old keys from `~/.ssh/authorized_keys` on the server.

# Setup

## To run project locally

1. checkout project from vcs: `git clone git@github.com:fredagscafeen/web.git`
2. setup virtual env: `python3 -mvenv ~/.cache/venvs/fredagscafeen-web`
3. activate virtual env: `source ~/.cache/venvs/fredagscafeen-web/bin/activate`
4. install `pip-tools`: `pip install pip-tools`
5. install dependencies: `pip-sync requirements.txt dev-requirements.txt`
6. install pre-commit hook: `pre-commit install`

Installing the required psycopg2 package (PostgreSQL for Python) might require the `pg_config` binary,
which can be installed on Ubuntu with `sudo apt install libpq-dev`.

7. migrate database: `./manage.py migrate`
8. create superuser: `./manage.py createsuperuser`
9. run server: `./manage.py runserver`

## Deploy changes

1. `git push`
2. Build docker image and redeploy: `ssh ubuntu@fredagscafeen.dk 'cd web && git pull && docker-compose build && docker-compose up -d'`

## Setup admin user on server

1. ssh into server: `ssh ubuntu@fredagscafeen.dk`
2. create superuser: `docker exec -it web_app_1 ./manage.py createsuperuser`
3. login to admin interface: [https://fredagscafeen.dk/admin/](https://fredagscafeen.dk/admin/)

# Github hook for automatically updating guide PDFs

- Generate a new ssh key: `ssh-keygen -t ed25519 -C github-action -f /tmp/github-action`
- Add the public key to the servers `~/.ssh/authorized_keys` file:
  `ssh ubuntu@fredagscafeen.dk 'cat >> ~/.ssh/authorized_keys' < /tmp/github-action.pub`
- Add Github action secrets on https://github.com/organizations/fredagscafeen/settings/secrets/actions:
  - Create the action secret `UPLOAD_SSH_KNOWN_HOSTS` containing the output of running:
    `grep fredagscafeen.dk ~/.ssh/known_hosts`
  - Create the action secret `UPLOAD_SSH_PRIVATE_KEY` containing the output of running:
    `cat /tmp/github-action`
  - Make sure both `guides` and `vedtægter` repos have access to these

Every time a tex file for a guide is updated, Github will recompile it and update the hosted PDF.

# Remote server printing

**TODO:** This needs to be updated.

## Diagram

```
+----------------------------------------------------+
| htlm5 server:                                      |
|                                                    |
| autossh -N -M 2244                                 |
|         -L 6631:localhost:631                      |
|         remoteprint@localhost                      |
|         -p 2222                          <-\       |
|         -v                                 |  ssh  |
|                                            |       |
|  +-----------------------------------------|---+   |
|  | dokku web instance:                     |   |   |
|  |                                             |   |
|  |                                             |   |
|  | ssh -o StrictHostKeyChecking=no             |   |
|  |     -i media/id_rsa                         |   |
|  |     remoteprint_relay@fredagscafeen.dk      |   |
|  |     --                                      |   |
|  |     lpstat -h localhost:6631 -E -p          |   |
|  |                                             |   |
|  +---------------------------------------------+   |
+----------------------------------------------------+
                     ^
                     |
                     |
       (reverse ssh port-forwarding)
                     |
                     |
+----------------------------------------------+
| remote AU server:                            |
|                                              |
| autossh -N -M 2233                           |
|         -R 2222:localhost:22                 |
|         remoteprint_relay@fredagscafeen.dk   |
|         -v                                   |
|                                              |
+----------------------------------------------+
```

## Installing autossh and cups

```sh
apt install autossh cups
systemctl disable --now cups
systemctl disable --now cups-browsed
```

## Setting up the reverse tunnel and ssh keys

Open 3 terminal windows:
* One connected to the remote machine on AU's network (remote)
* One connected to htlm5 (htlm5)
* One connected to htlm5 and inside the dokku container: `dokku run fredagscafeen.dk bash` (dokku)

Then run the following commands in order:

remote:
```sh
sudo useradd -m remoteprint
sudo mkhomedir_helper remoteprint
sudo -u remoteprint ssh-keygen
sudo cat /home/remoteprint/.ssh/id_rsa.pub # Key remote
```

dokku:
```sh
mkdir media/ssh
ssh-keygen -f media/ssh/id_rsa
cat media/ssh/id_rsa.pub # Key client
```

htlm5:
```sh
useradd -m remoteprint_relay
mkhomedir_helper remoteprint_relay
sudo -u remoteprint_relay ssh-keygen
cat /home/remoteprint_relay/.ssh/id_rsa.pub # Key relay

sudo -u remoteprint_relay sh -c 'echo "<Key remote>" >> /home/remoteprint_relay/.ssh/authorized_keys'
cat fredagscafeen-media/ssh/id_rsa.pub | sudo -u remoteprint_relay sh -c 'cat >> /home/remoteprint_relay/.ssh/authorized_keys'
```

remote:
```sh
sudo -u remoteprint sh -c 'echo "<Key relay>" >> /home/remoteprint/.ssh/authorized_keys'
```

Check that the remote can connect to the relay by running the following on the remote:
```sh
sudo -u remoteprint /usr/bin/autossh -N -M 2233 -R 2222:localhost:22 remoteprint_relay@fredagscafeen.dk -v
```

Check that we can connect to the relay and it can connect to the remote by running the following in dokku:
```sh
ssh -o StrictHostKeyChecking=no remoteprint_relay@fredagscafeen.dk -i media/ssh/id_rsa id
ssh -o StrictHostKeyChecking=no remoteprint_relay@fredagscafeen.dk -i media/ssh/id_rsa ssh remoteprint@localhost -p 2222 id
```

Stop the `autossh` command on the remote and create the file `/etc/systemd/system/remoteprinter_autossh.service` containing:
```ini
[Unit]
Description=Keeps a reverse tunnel to fredagscafeen.dk open
After=network-online.target
After=ssh.service
After=org.cups.cupsd.service

[Service]
ExecStart=/usr/bin/autossh -N -M 2233 -R 2222:localhost:22 remoteprint_relay@fredagscafeen.dk -v
Restart=on-failure
User=remoteprint
KillSignal=SIGINT
SendSIGKILL=no
Environment=AUTOSSH_GATETIME=0

[Install]
WantedBy=multi-user.target
```

Then start and enable the service on the remote:
```sh
sudo systemctl enable --now remoteprinter_autossh
```


Test that we can forward port 6631 to the remote's port 631 and it works (run both command at the same time on remote):
```sh
sudo -u /usr/bin/autossh -N -M 2244 -L 6631:localhost:631 remoteprint@localhost -p 2222 -v
lpstat -h localhost:6631 -p
```

Create the file `/etc/systemd/system/remoteprinter_cups_forward.service` containing:
```ini
[Unit]
Description=Forwards port 6631 to port 631 of an AU machine
After=network-online.target
After=ssh.service
After=org.cups.cupsd.service

[Service]
ExecStart=/usr/bin/autossh -N -M 2244 -L 6631:localhost:631 remoteprint@localhost -p 2222 -v
Restart=on-failure
User=remoteprint_relay
KillSignal=SIGINT
SendSIGKILL=no
Environment=AUTOSSH_GATETIME=0

[Install]
WantedBy=multi-user.target
```

Then start and enable the service on the remote:
```sh
sudo systemctl enable --now remoteprinter_cups_forward
```

## Limit remote to only allow forwarding to port 631

Add the following at the bottom of `/etc/ssh/sshd_config` on the remote:
```sh
Match User remoteprint
	AllowTcpForwarding yes
	X11Forwarding no
	PermitTunnel no
	GatewayPorts no
	AllowAgentForwarding no
	PermitOpen localhost:631
	ForceCommand echo 'This account can only be used for printing'
```

Then reload `sshd`:

```sh
systemctl reload sshd
```

## Setting up the printers to use

The printers should be installed on the remote machine and also be entered into the database.


# API usage

### Method Overview
> - Auth
> - Items
> - Breweries
> - BeerTypes
> - Bartenders
> - Is-Bartender

### Method details

#### **Auth**
POST <host>/api/auth/

##### Request
```
{
    "username": "...",
    "password": "..."
}
```
##### Response
```
{
    "token": "...",
    "permissions": [...]
}
```
-----------------

#### **Items**
GET <host>/api/items/

##### Response
```
[
    {
        "id": 871,
        "created": "2017-06-02T13:13:49Z",
        "name": "Semiskinned Occultist",
        "description": "",
        "country": "",
        "priceInDKK": 25.0,
        "abv": null,
        "container": null,
        "volumeInCentiliters": null,
        "inStock": true,
        "imageUrl": "",
        "barcode": "",
        "lastModified": "2017-06-02T13:14:53.756808Z",
        "link": "",
        "brewery": 16,
        "type": null
    },
    ...
]
```
-----------------

#### **Breweries**
GET <host>/api/breweries/

##### Response
```
[
    {
        "id": 1,
        "name": "Aarhus Bryghus",
        "description": "",
        "website": ""
    },
    ...
]
```
-----------------

#### **BeerTypes**
GET <host>/api/beerTypes/

##### Response
```
[
    {
        "id": 1,
        "name": "Pilsner",
        "description": "",
        "link": ""
    },
    ...
]
```
-----------------

#### **Bartenders**
GET <host>/api/bartenders/

##### Response
```
[
    {
        "id": 45,
        "name": "Alberte Herold Hansen",
        "username": "alberte",
        "isActiveBartender": true
    },
    ...
]
```
-----------------

#### **Is-Bartender**
GET <host>/api/is-bartender/<username>/

##### Response
```
true
```
-----------------
