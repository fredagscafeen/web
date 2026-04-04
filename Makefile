run:
	./manage.py runserver 0.0.0.0:8000
migrate:
	./manage.py migrate
migrations:
	./manage.py makemigrations
createsuperuser:
	./manage.py createsuperuser
import-db:
	./import_db
download-media:
	./download_media
makemessages:
	./manage.py makemessages --all
compilemessages:
	./manage.py compilemessages
