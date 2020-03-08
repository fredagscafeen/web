import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from bartenders.models import Bartender, BoardMemberPeriod

User = get_user_model()
GROUPS_FOR_NEW = [Group.objects.get(name="Alle i Bestyrelsen")]


class Command(BaseCommand):
    help = "Create/delete admin accounts"

    def add_arguments(self, parser):
        parser.add_argument("--no-delete", action="store_true")

    def handle(self, *args, **options):
        period = BoardMemberPeriod.get_current_period()
        board_member_bartenders = Bartender.objects.filter(board_members__period=period)

        users_to_keep = User.objects.filter(
            username__in=board_member_bartenders.values("username")
        )
        board_members_without_users = board_member_bartenders.exclude(
            username__in=users_to_keep.values("username")
        )
        if options["no_delete"]:
            users_to_delete = User.objects.none()
        else:
            users_to_delete = User.objects.filter(is_staff=True).exclude(
                id__in=users_to_keep
            )

        do_something = False
        if board_members_without_users.exists():
            do_something = True
            print("Users for the following bartenders will be created:")
            for bartender in board_members_without_users:
                print("", bartender)

            print()

        if users_to_delete.exists():
            do_something = True
            print("The following users will be deleted:")
            for user in users_to_delete:
                print("", user)

            print()

        if not do_something:
            print("Accounts are already updated.")
            return

        if input("Continue? [yN] ") not in ["y", "Y"]:
            return

        print("New users and passwords:")

        for bartender in board_members_without_users:
            first_name, last_name = bartender.name.split(maxsplit=1)
            user = User.objects.create(
                username=bartender.username,
                first_name=first_name,
                last_name=last_name,
                email=bartender.email,
                is_staff=True,
            )
            user.groups.set(GROUPS_FOR_NEW)
            password = secrets.token_hex(32)
            user.set_password(password)
            user.save()

            print(f"{bartender.username} {password}")

        users_to_delete.delete()
