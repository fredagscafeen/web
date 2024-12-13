from django import template

from bartenders.models import BartenderShift

register = template.Library()


@register.filter(name="is_current_week")
def is_current_week(shift):
    try:
        return shift.is_current_week()
    except BartenderShift.DoesNotExist:
        return False
