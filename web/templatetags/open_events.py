from django import template
from django.utils import timezone

from bartenders.models import Bartender
from events.models import Event, EventResponse
from web.templatetags.is_bartender import is_bartender

register = template.Library()


@register.filter("open_events")
def open_events(user):
    if not is_bartender(user):
        return 0
    bartender = Bartender.objects.get(email=user.email)
    events = Event.objects.all()
    events = events.filter(response_deadline__gte=timezone.now())
    events = events.exclude(responses__bartender=bartender)
    events = [event for event in events if event.may_attend(bartender)]
    return len(events)
