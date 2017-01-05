# Setup (wip)

## To run project locally using pycharm

1. checkout project from vcs
2. setup virtual env (commands should be run in project folder)
  `virtualenv web-venv`
  `source web-venv/bin/activate (not windows)`
  `./web-venv/scripts/activate (windows)`
  `pip install -r requirements.txt`

3. set env variables in pycharm
  `SECRET_KEY = "whatever"`
  `DJANGO_SETTINGS_MODULE = fredagscafeen.settings.local`
  
4. press green arrow to run

(database needs to be set as well, use migrate in Tools->Run manage.py Task)