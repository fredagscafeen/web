# Setup (WIP)

## To run project locally using pycharm

1. checkout project from vcs
2. setup virtual env (commands should be run in project folder)
  1. `pip3 install pipenv`
  2. `pipenv install`

Installing the required psycopg2 package (PostgreSQL for Python) might require the `pg_config` binary,
which can be installed on Ubuntu with `sudo apt install libpq-dev`.

3. set env variables in pycharm
  1. `SECRET_KEY = "whatever"`
  2. `DJANGO_SETTINGS_MODULE = fredagscafeen.settings.local`
  
4. press green arrow to run

(database needs to be set as well, use migrate in Tools->Run manage.py Task)

## Deploy changes

1. start pageant with private key used to log in to server

2. in project folder run `git push dokku master`

## API usage

#### Method Overview
> - Auth
> - Items
> - Breweries
> - BeerTypes
> - Bartenders
> - Is-Bartender

#### Method details

##### **Auth**
POST <host>/api/auth/

###### Request
```
{
    "username": "...",
    "password": "..."
}
```
###### Response
```
{
    "token": "...",
    "permissions": [...]
}
```
-----------------

##### **Items**
GET <host>/api/items/

###### Response
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

##### **Breweries**
GET <host>/api/breweries/

###### Response
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

##### **BeerTypes**
GET <host>/api/beerTypes/

###### Response
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

##### **Bartenders**
GET <host>/api/bartenders/

###### Response
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

##### **Is-Bartender**
GET <host>/api/is-bartender/<username>/

###### Response
```
true 
```
-----------------
