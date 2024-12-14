from django import template

from bartenders.models import BartenderShift

register = template.Library()


@register.filter(name="compare_to_current_week")
def compare_to_current_week(shift):
    try:
        return shift.compare_to_current_week()
    except BartenderShift.DoesNotExist:
        return False
