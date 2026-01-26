from django.conf import settings


def constants(request):
    return {
        "DOMAIN": settings.DOMAIN,
        "BEST_MAIL": settings.BEST_MAIL,
        "GIT_COMMIT_HASH": settings.GIT_COMMIT_HASH,
    }
