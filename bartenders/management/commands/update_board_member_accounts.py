import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from bartenders.models import Bartender, BoardMemberPeriod

User = get_user_model()
GROUPS_FOR_NEW = [Group.objects.get(name="Alle i Bestyrelsen")]


class Command(BaseCommand):
    help = "Create/delete admin accounts"

    @transaction.atomic
    def handle(self, *args, **options):
        period = BoardMemberPeriod.get_current_period()
        board_member_bartenders = Bartender.objects.filter(board_members__period=period)

        users_to_keep = User.objects.filter(
            username__in=board_member_bartenders.values("username")
        )
        users_to_delete = User.objects.filter(is_staff=True).exclude(
            id__in=users_to_keep
        )
        board_members_without_users = board_member_bartenders.exclude(
            username__in=users_to_keep.values("username")
        )

        print("Users for the following bartenders will be created:")
        for bartender in board_members_without_users:
            print("", bartender)

        print()
        print("The following users will be deleted:")
        for user in users_to_delete:
            print("", user)

        print()

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
