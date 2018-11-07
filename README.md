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

## TinyTex installation

This installs TinyTex and makes it available to the dokku django instance:

```
set tinytex /var/lib/dokku/data/storage/fredagscafeen-media/TinyTeX
rm -rf "$tinytex"

wget -qO- "https://yihui.name/gh/tinytex/tools/install-unx.sh" | sh

mv "$HOME/.TinyTeX" "$tinytex"
rm -rf "$HOME/bin"
```

We can now run `latexmk` inside the dokku django instance, by adding `/app/media/TinyTeX/bin/x86_64-linux` to the PATH.

## Installing needed LaTeX packages

TinyTex doesn't come with every LaTeX package we need, so we need to install these:

```
eval "$tinytex/bin/x86_64-linux/tlmgr" install was collectbox adjustbox truncate varwidth tabu colortbl xcolor microtype ifetex memoir pgf
```

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
