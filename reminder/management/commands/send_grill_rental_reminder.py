import datetime
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from reminder.management.commands._private import ReminderCommand
from udlejning.models import UdlejningGrill


class Command(ReminderCommand):
    help = "Sends grill rental reminders to responsible board members"

    def get_next_events(self):
        return UdlejningGrill.objects.filter(
            dateFrom__gte=timezone.now(),
            dateFrom__lte=timezone.now() + datetime.timedelta(7),
        )

    def get_bartenders_from_event(self, event):
        return event.bartendersInCharge.all()

    def email_subject(self, humanized_bartenders, event):
        return f"Du er ansvarlig for en udlejning af grillen i denne uge!"

    def email_body(self, humanized_bartenders, event):
        link = """Se mere i {link}."""
        return f"""Dette er en automatisk email.

Hej {humanized_bartenders}.

Du/I er ansvarlige for at leje grillen ud til {event.whoReserved}, {event.dateFrom.astimezone().strftime("d. %-d. %B, kl. %H:%M")}.

{link}

/snek"""

    def text_format(self, humanized_bartenders, event):
        url = urljoin(
            settings.SELF_URL,
            reverse("admin:udlejning_udlejninggrill_change", args=(event.pk,)),
        )
        return {"link": f"admin interfacet: {url}"}

    def html_format(self, humanized_bartenders, event):
        url = urljoin(
            settings.SELF_URL,
            reverse("admin:udlejning_udlejninggrill_change", args=(event.pk,)),
        )
        return {
            "link": mark_safe(f'<a href="{url}">admin interfacet</a>'),
        }

    def email_cc(self):
        return [f"udlejning@{settings.DOMAIN}"]

    def email_reply_to(self):
        return []
