from django.core.management.base import BaseCommand

from bartenders.models import BoardMember


class Command(BaseCommand):
    help = "Get previous and current best mails"

    def handle(self, *args, **options):
        board_members = BoardMember.objects.all()
        best = []
        for member in board_members:
            bartender = member.bartender
            print(f"{bartender.name} <{bartender.email}>")
            best.append(bartender)

        if not best:
            print("No board members found.")
            return

        print("mailto:", end=" ")
        for bartender in best:
            print(f'"{bartender.name}" <{bartender.email}>', end=", ")
