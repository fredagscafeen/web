# Setup (wip)

## To run project locally using pycharm

1. checkout project from vcs
2. setup virtual env (commands should be run in project folder)
  1. `virtualenv web-venv`
  2. `source web-venv/bin/activate (not windows)`
  3. `./web-venv/scripts/activate (windows)`
  4. `pip install -r requirements.txt`

3. set env variables in pycharm
  1. `SECRET_KEY = "whatever"`
  2. `DJANGO_SETTINGS_MODULE = fredagscafeen.settings.local`
  
4. press green arrow to run

(database needs to be set as well, use migrate in Tools->Run manage.py Task)

## Deploy changes

in project folder run
`git push dokku master`