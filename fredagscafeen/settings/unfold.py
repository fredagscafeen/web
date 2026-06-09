from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.contrib.constance.settings import UNFOLD_CONSTANCE_ADDITIONAL_FIELDS

UNFOLD = {
    "SITE_TITLE": "Fredagscafeen Admin",
    "SITE_HEADER": "Fredagscafeen Admin",
    "SITE_SUBHEADER": "Administration for Fredagscafeen",
    "SITE_DROPDOWN": [
        {
            "icon": "house",
            "title": _("Homepage"),
            "link": "/",
            "attrs": {
                "target": "_blank",
            },
        },
        {
            "icon": "archive",
            "title": _("S3 Storage Dashboard"),
            "link": "https://garage.fredagscafeen.dk",
            "attrs": {
                "target": "_blank",
            },
        },
        {
            "icon": "signpost",
            "title": "Traefik Dashboard",
            "link": "https://traefik.fredagscafeen.dk",
            "attrs": {
                "target": "_blank",
            },
        },
        {
            "icon": "cloud",
            "title": "Cloudflare DNS",
            "link": "https://dash.cloudflare.com/5a014495e995d95abe07b10e615244c0/fredagscafeen.dk/dns/records",
            "attrs": {
                "target": "_blank",
            },
        },
        {
            "icon": "deployed_code",
            "title": "GitHub Repository",
            "link": "https://github.com/fredagscafeen",
            "attrs": {
                "target": "_blank",
            },
        },
    ],
    "SITE_ICON": lambda request: static(
        "favicon.ico"
    ),  # both modes, optimise for 32px height
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("favicon.ico"),
        },
    ],
    "SHOW_HISTORY": True,  # show/hide "History" button
    "SHOW_VIEW_ON_SITE": True,  # show/hide "View on site" button
    "SHOW_BACK_BUTTON": True,  # show/hide "Back" button on changeform in header
    "SHOW_UI_WARNINGS": True,  # show/hide warnings in UI
    "SHOW_LANGUAGES": True,  # show/hide language selector in header
    "LOGIN": {
        "image": lambda request: static("images/login_bg.jpg"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
        "form": "fredagscafeen.forms.AdminLoginForm",
    },
    "STYLES": [
        lambda request: static("css/style.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/script.js"),
    ],
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "base": {
            # Cool-neutral grays with slight blue tint to complement #152ff5
            "50": "oklch(98.5% 0.003 264.5)",
            "100": "oklch(96.5% 0.006 264.5)",
            "200": "oklch(92.8% 0.010 264.5)",
            "300": "oklch(87.5% 0.015 264.5)",
            "400": "oklch(71.0% 0.022 264.5)",
            "500": "oklch(55.5% 0.027 264.5)",
            "600": "oklch(44.5% 0.028 264.5)",
            "700": "oklch(37.5% 0.030 264.5)",
            "800": "oklch(28.0% 0.028 264.5)",
            "900": "oklch(21.0% 0.025 264.5)",
            "950": "oklch(13.5% 0.020 264.5)",
        },
        "primary": {
            # Electric blue matching brand color #152ff5 at 500
            "50": "oklch(97.5% 0.016 264.5)",
            "100": "oklch(94.0% 0.040 264.5)",
            "200": "oklch(88.0% 0.085 264.5)",
            "300": "oklch(79.5% 0.155 264.5)",
            "400": "oklch(67.0% 0.225 264.5)",
            "500": "oklch(48.2% 0.276 264.5)",
            "600": "oklch(41.0% 0.258 264.5)",
            "700": "oklch(34.5% 0.230 264.5)",
            "800": "oklch(28.5% 0.190 264.5)",
            "900": "oklch(22.5% 0.145 264.5)",
            "950": "oklch(16.0% 0.095 264.5)",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "da": "🇩🇰",
            },
        },
    },
    "LANGUAGES": {
        "navigation": [
            {
                "bidi": False,
                "code": "da",
                "name": "Danish",
                "name_local": "Dansk",
                "name_translated": "Danish",
            },
            {
                "bidi": False,
                "code": "en",
                "name": "English",
                "name_local": "English",
                "name_translated": "English",
            },
        ],
    },
    "SIDEBAR": {
        "show_search": True,  # Search in applications and models names
        "command_search": True,  # Replace the sidebar search with the command search
        "show_all_applications": True,  # Dropdown with all applications and models
    },
    "COMMAND": {
        "search_models": True,  # Default: False
        "show_history": True,  # Enable history
    },
}

CONSTANCE_ADDITIONAL_FIELDS = {
    **UNFOLD_CONSTANCE_ADDITIONAL_FIELDS,
    str: [
        "django.forms.CharField",
        {
            "widget": "unfold.widgets.UnfoldAdminTextareaWidget",
            "required": False,
        },
    ],
}
