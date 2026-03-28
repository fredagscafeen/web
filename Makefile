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

