from celery import shared_task
from django.utils import timezone

from .models import ReleasedBartenderShift


@shared_task
def delete_old_released_bartender_shifts():
    return ReleasedBartenderShift.objects.filter(
        bartender_shift__end_datetime__lt=timezone.now()
    ).delete()
