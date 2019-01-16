from django import template

from bartenders.models import Bartender

register = template.Library()


@register.filter(name='is_with_user')
def is_with_user(shift, user):
    if not user.is_authenticated:
        return False

    try:
        bartender = Bartender.objects.get(email=user.email)
        return shift.is_with_bartender(bartender)
    except Bartender.DoesNotExist:
        return False

