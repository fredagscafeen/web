from django.conf import settings
from django.contrib.auth import get_user_model, login

User = get_user_model()


class AutologinMiddleware:
    def __init__(self, get_response):
        self.first_request = True
        self.get_response = get_response

    def __call__(self, request):

        if self.first_request:
            self.first_request = False

            username = getattr(settings, "AUTOLOGIN_USERNAME", None)
            if username:
                user = User.objects.get(username=username)
                login(request, user, "django.contrib.auth.backends.ModelBackend")

        return self.get_response(request)
