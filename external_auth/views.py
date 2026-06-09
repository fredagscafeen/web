from urllib.parse import quote, urlparse

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def traefik_auth_verify(request):
    protocol = request.headers.get("X-Forwarded-Proto", "https")
    host = request.headers.get("X-Forwarded-Host", "")
    uri = request.headers.get("X-Forwarded-Uri", "")
    original_url = f"{protocol}://{host}{uri}"

    relay_path = reverse("auth-relay") + "?to=" + quote(original_url)
    login_url = f"https://{settings.DOMAIN}{reverse('admin:login')}"
    target_redirect = f"{login_url}?next={quote(relay_path)}"

    if not request.user.is_authenticated:
        return HttpResponseRedirect(target_redirect)

    subdomain = host.split(".")[0] if "." in host else ""

    if (
        request.user.has_perm("external_auth.view_" + subdomain)
        or request.user.is_superuser
    ):
        response = HttpResponse("OK", status=200)
        response["X-WEBAUTH-USER"] = request.user.username
        return response

    return HttpResponse(
        "Forbidden: You do not have access to this service.", status=403
    )


def auth_relay(request):
    to = request.GET.get("to", "")
    try:
        parsed = urlparse(to)
        host = parsed.hostname or ""
        if host == settings.DOMAIN or host.endswith("." + settings.DOMAIN):
            return HttpResponseRedirect(to)
    except Exception:
        pass
    return HttpResponseRedirect(f"https://{settings.DOMAIN}/")
