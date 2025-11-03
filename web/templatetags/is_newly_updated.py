import datetime

from django import template
from django.utils import timezone

register = template.Library()


@register.filter(name="is_newly_updated")
def is_newly_updated(guide):
    date = timezone.now().date()
    return date - guide.updated_at <= datetime.timedelta(days=365)
