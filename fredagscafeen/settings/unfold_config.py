from django.templatetags.static import static

# Unfold admin interface settings
UNFOLD = {
    "DARK_MODE": True,
    "SITE_TITLE": "Fredagscafeen Admin",
    "SITE_HEADER": "Fredagscafeen",
    "SITE_SUBHEADER": "Administration for Fredagscafeen",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "SITE_DROPDOWN": [
        {
            "icon": "bi bi-house-fill",
            "title": "Go to website",
            "link": "https://fredagscafeen.dk/",
        },
        {
            "icon": "bi bi-book-half",
            "title": "Guides",
            "link": "https://fredagscafeen.dk/guides",
        },
    ],
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: static("/images/logo.png"),  # light mode
        "dark": lambda request: static("/images/logo.png"),  # dark mode
    },
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "base": {
            "50": "#fafaf9",
            "100": "#f5f5f4",
            "200": "#e7e5e4",
            "300": "#d6d3d1",
            "400": "#a6a09b",
            "500": "#79716b",
            "600": "#57534d",
            "700": "#44403b",
            "800": "#292524",
            "900": "#1c1917",
            "950": "#0c0a09",
        },
        "primary": {
            "50": "#eff6ff",
            "100": "#dbeafe",
            "300": "#90c5ff",
            "400": "#54a2ff",
            "500": "#3080ff",
            "600": "#155dfc",
            "700": "#1447e6",
            "800": "#193cb8",
            "900": "#1c398e",
            # "950": "#162456",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",  # text-base-500
            "subtle-dark": "var(--color-base-400)",  # text-base-400
            "default-light": "var(--color-base-600)",  # text-base-600
            "default-dark": "var(--color-base-300)",  # text-base-300
            "important-light": "var(--color-base-900)",  # text-base-900
            "important-dark": "var(--color-base-100)",  # text-base-100
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "dk": "🇩🇰",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
    },
}
