from django import template

from email_auth.auth import EmailTokenBackend

register = template.Library()


@register.filter(name="is_bartender")
def is_bartender(user):
    if not user.is_authenticated:
        return False
    return EmailTokenBackend.is_bartender(user.email)
