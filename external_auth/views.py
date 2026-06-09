from urllib.parse import quote

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def traefik_auth_verify(request):
    protocol = request.headers.get("X-Forwarded-Proto", "https")
    host = request.headers.get("X-Forwarded-Host", "")
    uri = request.headers.get("X-Forwarded-Uri", "")
    original_url = f"{protocol}://{host}{uri}"

    login_url = request.build_absolute_uri(reverse("admin:login"))

    target_redirect = f"{login_url}?next={quote(original_url)}"

    if not request.user.is_authenticated:
        return HttpResponseRedirect(target_redirect)

    subdomain = host.split(".")[0] if "." in host else ""

    # Allow access if the user has the specific view_<subdomain> permission or is a superuser
    if (
        request.user.has_perm("external_auth.view_" + subdomain)
        or request.user.is_superuser
    ):
        response = HttpResponse("OK", status=200)
        response["X-WEBAUTH-USER"] = request.user.username
        return response

    # If they are logged in but lack the specific permission for this host:
    return HttpResponse(
        "Forbidden: You do not have access to this service.", status=403
    )
