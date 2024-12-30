from django import template

from bartenders.models import Bartender

register = template.Library()


@register.filter(name="is_bartender")
def is_bartender(user):
    if not user.is_authenticated:
        return False

    try:
        bartender = Bartender.objects.get(email=user.email)
        return bartender is not None
    except Bartender.DoesNotExist:
        return False
