from django import template

from events.models import Event

register = template.Library()


@register.filter(name="event_info")
def event_info(shift):
    if not shift or not getattr(shift, "start_datetime", None):
        return None

    return Event.objects.filter(
        start_datetime__date=shift.start_datetime.date(),
        event_type=Event.EventType.COMMON,
    ).first()
