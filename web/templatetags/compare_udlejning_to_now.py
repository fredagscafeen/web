from django import template
from django.utils import timezone

from udlejning.models import Udlejning

register = template.Library()


@register.filter(name="compare_udlejning_to_now")
def compare_udlejning_to_now(udlejning):
    try:
        return udlejning.dateFrom.date() >= timezone.now().date()
    except Udlejning.DoesNotExist:
        return False
