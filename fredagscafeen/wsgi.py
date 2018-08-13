import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fredagscafeen.settings.htlm5")

application = get_wsgi_application()
