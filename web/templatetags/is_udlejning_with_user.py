from django import template

from bartenders.models import Bartender
from udlejning.models import Udlejning

register = template.Library()


@register.filter(name="is_udlejning_with_user")
def is_with_user(udlejning, user):
    if not user.is_authenticated:
        return False

    try:
        bartender = Bartender.objects.get(email=user.email)
        return udlejning.is_with_user(bartender)
    except Udlejning.DoesNotExist:
        return False
