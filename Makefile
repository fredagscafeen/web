run:
	./manage.py runserver 0.0.0.0:8000
migrate:
	./manage.py migrate
gen-items-migrations:
	./manage.py makemigrations items
createsuperuser:
	./manage.py createsuperuser
import-db:
	./import_db
download-media:
	./download_media
translate:
	./manage.py makemessages -d django -l da -l en
	./manage.py makemessages -d djangojs -l da -l en
	./manage.py compilemessages
