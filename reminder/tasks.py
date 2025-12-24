from celery import shared_task

from .management.commands.send_barshift_reminder import (
    Command as BarshiftReminderCommand,
)
from .management.commands.send_boardgamecart_rental_reminder import (
    Command as BoardGameCartRentalReminderCommand,
)
from .management.commands.send_grill_rental_reminder import (
    Command as GrillRentalReminderCommand,
)
from .management.commands.send_pantvagt_reminder import (
    Command as PantvagtReminderCommand,
)
from .management.commands.send_projector_rental_reminder import (
    Command as ProjectorRentalReminderCommand,
)
from .management.commands.send_rental_reminder import Command as RentalReminderCommand
from .management.commands.send_speakers_rental_reminder import (
    Command as SpeakersRentalReminderCommand,
)
from .management.commands.send_tent_rental_reminder import (
    Command as TentRentalReminderCommand,
)


@shared_task
def send_barshift_reminder():
    c = BarshiftReminderCommand()
    c.run_from_argv(["", ""])


@shared_task
def send_pantvagt_reminder():
    c = PantvagtReminderCommand()
    c.run_from_argv(["", ""])


@shared_task
def send_rental_reminder():
    c = RentalReminderCommand()
    c.run_from_argv(["", ""])


@shared_task
def send_projector_rental_reminder():
    c = ProjectorRentalReminderCommand()
    c.run_from_argv(["", ""])


@shared_task
def send_grill_rental_reminder():
    c = GrillRentalReminderCommand()
    c.run_from_argv(["", ""])


@shared_task
def send_speakers_rental_reminder():
    c = SpeakersRentalReminderCommand()
    c.run_from_argv(["", ""])


@shared_task
def send_tent_rental_reminder():
    c = TentRentalReminderCommand()
    c.run_from_argv(["", ""])


@shared_task
def send_boardgamecart_rental_reminder():
    c = BoardGameCartRentalReminderCommand()
    c.run_from_argv(["", ""])
