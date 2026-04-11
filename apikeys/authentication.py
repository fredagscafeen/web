from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions
from rest_framework.authtoken.models import Token

from apikeys.models import GranularAPIKey
from apikeys.permissions import BearerKeyParser


class BearerTokenAuthentication(authentication.TokenAuthentication):
    keyword = BearerKeyParser.keyword

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.select_related("user").get(key=key)
        except Token.DoesNotExist:
            return None

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted.")

        return (token.user, token)


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
