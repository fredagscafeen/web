from django import template

from events.models import Event

register = template.Library()


@register.filter(name="event_info")
def event_info(shift):
    if not shift or not getattr(shift, "start_datetime", None):
        return None

    shift_date = shift.start_datetime.date()

    return Event.objects.filter(start_datetime__date=shift_date).first()
