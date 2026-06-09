from django.urls import path

from external_auth.views import auth_bridge, traefik_auth_verify

urlpatterns = [
    path("verify/", traefik_auth_verify, name="traefik-auth-verify"),
    path("bridge/", auth_bridge, name="auth-bridge"),
]
