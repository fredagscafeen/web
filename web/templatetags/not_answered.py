from django import template
from django.utils import timezone

from bartenders.models import Bartender
from events.models import Event, EventResponse
from web.templatetags import is_bartender

register = template.Library()


@register.filter("not_answered")
def not_answered(user, event):
    if not is_bartender.is_bartender(user):
        return False
    bartender = Bartender.objects.get(email=user.email)
    events = Event.objects.filter(pk=event.pk)
    events = events.exclude(responses__bartender=bartender)
    return len(events) > 0
