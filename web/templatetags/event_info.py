from django import template

from bartenders.models import BartenderShift
from events.models import CommonEvent

register = template.Library()


@register.filter(name="event_info")
def event_info(shift):
    try:
        return CommonEvent.objects.filter(date=shift.start_datetime.date()).first()
    except BartenderShift.DoesNotExist:
        return None
