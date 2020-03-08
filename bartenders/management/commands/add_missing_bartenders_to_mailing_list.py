from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bartenders.mailman2 import Mailman
from bartenders.models import Bartender


class Command(BaseCommand):
    help = "Add all bartenders who is not on the all list to it"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        mailman = Mailman(
            settings.MAILMAN_URL_BASE,
            settings.MAILMAN_ALL_LIST,
            settings.MAILMAN_ALL_PASSWORD,
        )

        subscribers = set(s.lower() for s in mailman.get_subscribers())

        newest_bartenders = Bartender.objects.order_by("-pk").filter(
            isActiveBartender=True
        )

        batch_emails = []
        add_all = False
        for b in newest_bartenders:
            email = b.email.lower()
            if email not in subscribers:
                email_formatted = f"{b.name} <{email}>"
                print(f"Missing: {email_formatted}")
                batch_emails.append(email_formatted)
                continue

            if not batch_emails:
                continue

            while True:
                if options["dry_run"]:
                    ans = "n"
                elif add_all:
                    ans = "a"
                else:
                    ans = input("Add above to mailing list? [y/n/D/a] ").lower()

                if ans == "":
                    ans = "d"

                if ans not in "ynda":
                    print(f"Invalid answer: {ans}")
                else:
                    break

            print()

            if ans in "ya":
                mailman.add_subscriptions(batch_emails)
                if ans == "a":
                    add_all = True

            batch_emails = []

            if ans == "d":
                break
