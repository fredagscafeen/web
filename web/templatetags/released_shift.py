from django import template

from bartenders.models import ReleasedBartenderShift

register = template.Library()


@register.filter(name="released_shift")
def released_shift(bartender, shift):
    try:
        return ReleasedBartenderShift.objects.get(
            bartender=bartender, bartender_shift=shift
        )
    except ReleasedBartenderShift.DoesNotExist:
        return None
