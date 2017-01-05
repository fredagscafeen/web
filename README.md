# Setup (wip)

## To run project locally using pycharm

1. checkout project from vcs
2. setup virtual env (commands should be run in project folder)
  i. `virtualenv web-venv`
  ii. `source web-venv/bin/activate (not windows)`
  iii. `./web-venv/scripts/activate (windows)`
  iv. `pip install -r requirements.txt`

3. set env variables in pycharm
  i. `SECRET_KEY = "whatever"`
  ii. `DJANGO_SETTINGS_MODULE = fredagscafeen.settings.local`
  
4. press green arrow to run

(database needs to be set as well, use migrate in Tools->Run manage.py Task)