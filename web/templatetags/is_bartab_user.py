from django import template

from email_auth.auth import EmailTokenBackend

register = template.Library()


@register.filter(name="is_bartab_user")
def is_bartab_user(user):
    if not user.is_authenticated:
        return False
    return EmailTokenBackend.is_bartab_user(user.email)
