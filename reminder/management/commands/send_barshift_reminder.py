import datetime

import requests
from django.utils import timezone

from bartenders.models import BartenderShift, date_format
from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = "Send barshift reminder emails to bartenders for the upcoming friday"

    def get_next_events(self):
        return BartenderShift.objects.filter(
            end_datetime__gte=timezone.now(),
            end_datetime__lte=timezone.now() + datetime.timedelta(7),
        )

    def get_bartenders_from_event(self, event):
        return event.all_bartenders()

    def email_subject(self, humanized_bartenders, event):
        return "Du har en barvagt på fredag!"

    def get_spotlight(self):
        # Fetch the CSV file from the URL
        # url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQyLNygOIGu63LRFXuDrQk16sUjzqfAP_6QXllAp5DO3AVVRz9i9_kHPcW20qTthnbOOOVHNxFWf8TT/pub?gid=1786763503&single=true&output=csv"
        url = "https://script.google.com/macros/s/AKfycbxmPCCxcAJsmH1NTFhme-AWfd6_8FP0D1Ba7Kv0I-b8qwUK_rWx6ktPRt5ydtb4uCQRkA/exec"
        try:
            response = requests.get(url)
            if response.status_code != 200:
                return ""
            beers = response.json().get("beer")

            final_text = f"Vi har {len(beers)} øl i spotlight i denne uge:\n\n"
            for beer in beers:
                _type = beer.get("type")
                name = beer.get("name")
                cost = beer.get("price")
                notes = beer.get("notes")

                final_text += f"{name}\n - Type: {_type} \n - Smagsnoter: {notes} \n - Pris: {cost:.2f} kr \n\n"
            print(final_text)
            return final_text
        except Exception as e:
            print(f"Error fetching spotlight data: {e}")
            return ""

    def email_body(self, humanized_bartenders, event):
        start = event.start_datetime - datetime.timedelta(minutes=30)
        start_time = date_format(start, "H:i")

        return f"""Hej {humanized_bartenders}.

Den kommende fredag er det JERES tur til at stå i Fredagscaféen.
Dette er en automatisk email sendt til jer og bestyrelsen.
Emailen er hovedsageligt sendt så I kan finde en anden at bytte vagt med,
hvis en af jer ikke har mulighed for selv at tage den.
Husk at jeres vagt starter kl. {start_time}.

Ses i baren!

/Bestyrelsen"""

    def email_reply_to(self):
        return ["alle@fredagscafeen.dk"]
