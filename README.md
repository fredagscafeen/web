# Setup (WIP)

## To run project locally

1. checkout project from vcs: `git clone git@gitlab.au.dk:fredagscafeen/web.git`
2. setup virtual env (commands should be run in project folder)
  1. `pip3 install pipenv`
  2. `pipenv install`

Installing the required psycopg2 package (PostgreSQL for Python) might require the `pg_config` binary,
which can be installed on Ubuntu with `sudo apt install libpq-dev`.

3. activate virtualenv: `pipenv shell`
4. migrate database: `./manage.py migrate`
5. create superuser: `./manage.py createsuperuser`
6. run server: `./manage.py runserver`

## Deploy changes

1. Add your SSH key to dokku: `ssh root@fredagscafeen.dk "dokku ssh-keys:add $USER" < ~/.ssh/id_rsa.pub`
2. Add dokku remote: `git remote add dokku dokku@fredagscafeen.dk:fredagscafeen.dk`
3. `git push dokku master`

## Setup admin user on server

1. ssh into server: `ssh root@fredagscafeen.dk`
2. create superuser: `dokku run fredagscafeen.dk ./manage.py createsuperuser`
3. login to admin interface: [https://fredagscafeen.dk/admin/](https://fredagscafeen.dk/admin/)

# LaTeX installation

This installs TeX Live full and makes it available to the dokku django instance:

```
set -x TEXLIVE_INSTALL_PREFIX /var/lib/dokku/data/storage/fredagscafeen-media/texlive
rm -rf "$TEXLIVE_INSTALL_PREFIX"

cd /tmp
curl -L http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz -o install-tl.tar.gz
tar -xzf install-tl.tar.gz
cd install-tl-*
./install-tl -scheme full -profile /dev/null -repository https://ctan.mirror.norbert-ruehl.de/systems/texlive/tlnet/
```

We need to specify a mirror located in Germany (as the server) as otherwise it defaults to some Australian mirror.

# Remote server printing

## Installing autossh and cups

```
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
```
sudo useradd -m remoteprint
sudo mkhomedir_helper remoteprint
sudo -u remoteprint ssh-keygen
sudo cat /home/remoteprint/.ssh/id_rsa.pub # Key remote
```

dokku:
```
mkdir media/ssh
ssh-keygen -f media/ssh/id_rsa
cat media/ssh/id_rsa.pub # Key client
```

htlm5:
```
useradd -m remoteprint_relay
mkhomedir_helper remoteprint_relay
sudo -u remoteprint_relay ssh-keygen
cat /home/remoteprint_relay/.ssh/id_rsa.pub # Key relay

sudo -u remoteprint_relay sh -c 'echo "<Key remote>" >> /home/remoteprint_relay/.ssh/authorized_keys'
cat fredagscafeen-media/ssh/id_rsa.pub | sudo -u remoteprint_relay sh -c 'cat >> /home/remoteprint_relay/.ssh/authorized_keys'
```

remote:
```
sudo -u remoteprint sh -c 'echo "<Key relay>" >> /home/remoteprint/.ssh/authorized_keys'
```

Check that the remote can connect to the relay by running the following on the remote:
```
sudo -u remoteprint autossh -M 0 -R 2222:localhost:22 -N remoteprint_relay@fredagscafeen.dk -v
```

Check that we can connect to the relay and it can connect to the remote by running the following in dokku:
```
ssh -o StrictHostKeyChecking=no remoteprint_relay@fredagscafeen.dk -i media/ssh/id_rsa id
ssh -o StrictHostKeyChecking=no remoteprint_relay@fredagscafeen.dk -i media/ssh/id_rsa ssh remoteprint@localhost -p 2222 id
```

Stop the `autossh` command on the remote and create the file `/etc/systemd/system/remoteprinter_autossh.service` containing:
```
[Unit]
Description=Keeps a reverse tunnel to fredagscafeen.dk open
After=network-online.target ssh.service

[Service]
User=remoteprint
ExecStart=/usr/bin/autossh -N -M 0 -R 2222:localhost:22 remoteprint_relay@fredagscafeen.dk -v
ExecStop=/bin/kill $MAINPID

[Install]
WantedBy=multi-user.target
```

Then start and enable the service on the remote:
```
sudo systemctl enable --now remoteprinter_autossh
```


Test that we can forward port 6631 to the remote's port 631 and it works (run both command at the same time on remote):
```
sudo -u remoteprint_relay autossh -N -M 0 remoteprint@localhost -p 2222 -L 6631:localhost:631 -v
lpstat -h localhost:6631 -p
```

Create the file `/etc/systemd/system/remoteprinter_cups_forward.service` containing:
```
[Unit]
Description=Forwards port 6631 to port 631 of an AU machine
After=network-online.target ssh.service

[Service]
User=remoteprint_relay
ExecStart=/usr/bin/autossh -N -M 0 remoteprint@localhost -p 2222 -L 6631:localhost:631 -v
ExecStop=/bin/kill $MAINPID

[Install]
WantedBy=multi-user.target
```

Then start and enable the service on the remote:
```
sudo systemctl enable --now remoteprinter_cups_forward
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
