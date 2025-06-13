from celery import shared_task

from .management.commands.send_barshift_reminder import (
    Command as BarshiftReminderCommand,
)
from .management.commands.send_pantvagt_reminder import (
    Command as PantvagtReminderCommand,
)
from .management.commands.send_udlejning_reminder import (
    Command as UdlejningReminderCommand,
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
def send_udlejning_reminder():
    c = UdlejningReminderCommand()
    c.run_from_argv(["", ""])
