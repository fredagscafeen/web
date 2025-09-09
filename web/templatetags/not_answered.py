from django import template
from django.utils import timezone

from bartenders.models import Bartender
from events.models import Event
from web.templatetags.is_bartender import is_bartender

register = template.Library()


@register.filter("not_answered")
def not_answered(user, event):
    if not is_bartender(user):
        return False
    bartender = Bartender.objects.get(email=user.email)
    events = Event.objects.filter(
        pk=event.pk,
        response_deadline__gte=timezone.now(),
    )
    events = events.exclude(responses__bartender=bartender)
    return len(events) > 0
