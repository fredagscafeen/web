from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions

from apikeys.models import GranularAPIKey
from apikeys.permissions import BearerKeyParser


class GranularAPIKeyAuthentication(authentication.BaseAuthentication):
    key_parser = BearerKeyParser()

    def authenticate(self, request):
        key = self.key_parser.get(request)
        if key is None:
            return None

        if not GranularAPIKey.objects.is_valid(key):
            raise exceptions.AuthenticationFailed("Invalid API key.")

        api_key = GranularAPIKey.objects.get_from_key(key)
        return (AnonymousUser(), api_key)

    def authenticate_header(self, request):
        return self.key_parser.keyword
