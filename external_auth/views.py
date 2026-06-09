from urllib.parse import urlencode, urlparse

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def traefik_auth_verify(request):
    protocol = request.headers.get("X-Forwarded-Proto", "https")
    host = request.headers.get("X-Forwarded-Host", "")
    uri = request.headers.get("X-Forwarded-Uri", "")
    original_url = f"{protocol}://{host}{uri}"

    if not request.user.is_authenticated:
        bridge_url = f"https://{settings.DOMAIN}{reverse('auth-bridge')}?{urlencode({'to': original_url})}"
        return HttpResponseRedirect(bridge_url)

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


def auth_bridge(request):
    to = request.GET.get("to", "")

    try:
        parsed = urlparse(to)
        host = parsed.hostname or ""
        valid = host == settings.DOMAIN or host.endswith("." + settings.DOMAIN)
    except Exception:
        valid = False

    if not valid:
        return HttpResponseRedirect(f"https://{settings.DOMAIN}/")

    if request.user.is_authenticated:
        # Cycle session key so the response sets a fresh cookie with
        # SESSION_COOKIE_DOMAIN=".fredagscafeen.dk", fixing old cookies that
        # lacked subdomain scope and couldn't reach the forwardAuth endpoint.
        request.session.cycle_key()
        return HttpResponseRedirect(to)

    bridge_next = reverse("auth-bridge") + "?" + urlencode({"to": to})
    login_url = f"https://{settings.DOMAIN}{reverse('admin:login')}"
    return HttpResponseRedirect(f"{login_url}?{urlencode({'next': bridge_next})}")
