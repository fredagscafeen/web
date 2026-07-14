from django import template

from email_auth.auth import EmailTokenBackend

register = template.Library()


@register.filter(name="event_description")
def event_description(event, user):
    if not event or not user:
        return None

    if user.is_authenticated and EmailTokenBackend.is_bartender(user.email):
        return event.internal_description or event.description
    else:
        return event.description
