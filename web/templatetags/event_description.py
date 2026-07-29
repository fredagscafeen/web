from django import template

from email_auth.auth import EmailTokenBackend

register = template.Library()

MAX_DESCRIPTION_LENGTH_SHOWN = 200


@register.filter(name="event_description")
def event_description(event, user):
    if not event or not user:
        return None

    if user.is_authenticated and EmailTokenBackend.is_bartender(user.email):
        return trim_description(event.internal_description)

    return trim_description(event.description)


def trim_description(description):
    if not description:
        return None

    if len(description) > MAX_DESCRIPTION_LENGTH_SHOWN:
        return description[0:MAX_DESCRIPTION_LENGTH_SHOWN] + "..."
    return description
