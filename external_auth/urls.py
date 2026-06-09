from django.urls import path

from external_auth.views import traefik_auth_verify

urlpatterns = [
    path("verify/", traefik_auth_verify, name="traefik-auth-verify"),
]
