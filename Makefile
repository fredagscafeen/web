.PHONY: deploy logs run migrate migrations createsuperuser import-db download-media makemessages compilemessages test new-module

deploy:
	docker-compose pull
	docker-compose up -d --remove-orphans
logs:
	tail -f django.log
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
test:
	./manage.py test
new-module:
	echo "Enter module name: " && read module && ./manage.py startapp $$module
