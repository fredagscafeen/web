import sys

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db.models import Q

from bartab.models import BarTabUser


class Command(BaseCommand):
    help = "Send bartab mails"

    def should_send_mail(self, bartab_user):
        if bartab_user.balance > -50:
            return False

        real_snapshots = bartab_user.entries.filter(~Q(snapshot__bartender_shift=None))
        if real_snapshots.exists():
            return False

        if not bartab_user.email:
            print(f"No email for: {bartab_user.name}", file=sys.stderr)
            return False

        return True

    def send_mail(self, bartab_user):
        email = EmailMessage(
            subject="Krydsliste i Fredagscaféen",
            from_email="form@fredagscafeen.dk",
            to=[bartab_user.email],
            reply_to=["form@fredagscafeen.dk"],
            body=f"""Hej {bartab_user.name},

Jeg er i gang med at indkræve gammel krydslistegæld i Fredagscaféen, da vi ikke tillader negative balancer, men har meget udestående gæld.
Din balance er {round(bartab_user.balance, 2)} kr. på vores krydsliste.

Det letteste ville være hvis du kom i fredagscaféen en fredag og betalte din gæld med kort eller kontanter.
Hvis dette ikke er muligt så skriv endelig tilbage, så kan vi finde ud af noget med at mobilepaye mig personligt,
eller at du sender direkte til vores bankkonto.

Venlig hilsen,
Anders Bruun Severinsen - formand i fredagscaféen""",
        )
        email.send()

    def handle(self, *args, **options):
        users = []
        total = 0
        for b in BarTabUser.objects.all():
            if self.should_send_mail(b):
                users.append(b)
                print(f"{b.name}: {round(b.balance, 2)}")
                total += b.balance

        print()
        print(f"Total: {total}")

        if input("Send mails? ").lower() != "y":
            return

        for b in users:
            self.send_mail(b)
