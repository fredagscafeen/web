from django.urls import path

from external_auth.views import auth_relay, traefik_auth_verify

urlpatterns = [
    path("verify/", traefik_auth_verify, name="traefik-auth-verify"),
    path("relay/", auth_relay, name="auth-relay"),
]
