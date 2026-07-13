from django import template

from events.models import Event

register = template.Library()


@register.filter(name="event_info")
def event_info(shift):
    try:
        return Event.objects.filter(
            date=shift.start_datetime.date(), event_type=Event.EventType.COMMON
        ).first()
    except Event.DoesNotExist:
        return None
