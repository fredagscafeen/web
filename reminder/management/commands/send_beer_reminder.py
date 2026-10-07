import datetime

from constance import config
from django.conf import settings
from django.utils import timezone

from fredagscafeen.email import send_template_email
from items.models import Item
from reminder.management.commands._private import BaseCommand

DAYS_TO_CONSIDER_SOON = 31


class Command(BaseCommand):
    help = "Send beer reminder email to responsible board members for the upcoming week"

    def handle(self, *args, **options):
        if not config.SEND_REMINDERS:
            print("SEND_REMINDERS is false, not sending any reminders.")
            return

        today = timezone.localdate()
        itemsExpiringSoon = Item.objects.filter(
            bestBefore__lte=today + datetime.timedelta(DAYS_TO_CONSIDER_SOON),
            inStock=True,
        ).order_by("bestBefore")

        itemsExpiringSoon_info = ""
        if itemsExpiringSoon.exists():
            itemsExpiringSoon_info += f"""
De følgende varer udløber snart. Tjek, om vi stadig har dem på lager, eller om bedst før-datoen skal opdateres.
"""
            for item in itemsExpiringSoon:
                item_info = f'"{item.name}", {item.type} ({item.brewery})'
                if item.bestBefore is None:
                    itemsExpiringSoon_info += (
                        f" -\t(INGEN BEDST FØR DATO!) {item_info}\n"
                    )
                    continue
                elif item.bestBefore == today:
                    itemsExpiringSoon_info += f" -\t(UDLØBER I DAG!) {item_info}\n"
                elif item.bestBefore < today:
                    itemsExpiringSoon_info += f" -\t(UDLØBET!) {item_info}\n"
                else:
                    days_until_expiration = (item.bestBefore - today).days
                    itemsExpiringSoon_info += f" -\t(UDLØBER {"I MORGEN!" if days_until_expiration == 1 else f"OM {days_until_expiration} DAGE"}) {item_info}\n"

        body_template = f"""Dette er en automatisk email.

Husk at opdatere månedens øl og ugens spotlight.
 -\tMånedens øl er den øl, vi gerne vil have solgt mest af i den kommende periode.
\tDet er også den øl, man kan finde på hjulet i baren, så prisen på denne øl skal ligge omkring 30 kr., så hjulet går i nul.
 -\tUgens spotlight kan bruges til varer, vi gerne vil have solgt ud af, hvis de f.eks. er ved at overskride deres bedst før-dato.
\tDet kan også bruges til at fremhæve en øl, vi gerne vil have solgt mere af.
{itemsExpiringSoon_info}
Husk, at bare fordi en vare har overskredet sin bedst før-dato, må vi stadig gerne sælge den,
så længe den ikke er dårlig, og vi gør opmærksom på, at den har overskredet sin bedst før-dato.
Hvis den har overskredet datoen, kan man overveje at sætte prisen ned, så vi får solgt den.

/snek"""

        send_template_email(
            subject=f"{len(itemsExpiringSoon)} varer nærmer sig bedst før-datoen. Husk at opdatere månedens øl og ugens spotlight",
            body_template=body_template,
            to=[f"beer@{settings.DOMAIN}"],
            cc=[f"reminder@{settings.DOMAIN}"],
            reply_to=[f"best@{settings.DOMAIN}"],
        )

        print(f"Reminder sent to the beer mailing list!")
