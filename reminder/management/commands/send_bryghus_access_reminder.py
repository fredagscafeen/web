from constance import config
from django.conf import settings
from django.core.management.base import BaseCommand

from fredagscafeen.email import send_template_email
from mail.models import MailingList


class Command(BaseCommand):
    help = "Sends a reminder to the beer mailing list with a notification about refreshing the Aarhus Bryghus external card access"

    def handle(self, *args, **options):
        if not config.SEND_REMINDERS:
            print("SEND_REMINDERS is false, not sending any reminders.")
            return

        body_template = """
Det er blevet tid til at forny Aarhus Bryghus' adgangskort til p-kælderen!

Dette skal gøres hver 3. måned, og kortet udløber omkring d. 29. i måneden.

Det fornyes ved at skrive til Tina (rudolph@cs.au.dk) eller Mette (mmd@cs.au.dk). Alternativt kan cardaccess@cs.au.dk også videresende opgaven.

Fra du sender mailen, skal opgaven sendes videre til en centraladminstration. Dette kan tage op til en uge, så skriv med det samme til én af de ovenstående!

Aarhus Bryghus' kort har følgende oplysninger:
EXTERNAL IDENTITY CARD
Aarhus Bryghus Fredagscafe, øl-depot ADA
Kortnr. 060546
Nummer ved magnetstribe: 106820
"""

        send_template_email(
            subject="VIGTIGT: Aarhus Bryghus adgang udløber!",
            body_template=body_template,
            to=[f"beer@{settings.DOMAIN}"],
            cc=[f"reminder@{settings.DOMAIN}"],
            reply_to=[f"best@{settings.DOMAIN}"],
        )

        print(f"Reminders sent to the beer mailing list!")
