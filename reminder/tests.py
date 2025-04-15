import datetime

from django.test import TestCase
from django.utils import timezone

from .management.commands.send_barshift_reminder import (
    Command as BarshiftReminderCommand,
)


# Create your tests here.
class BarshiftReminderTests(TestCase):
    def setUp(self):
        self.test_reminder = BarshiftReminderCommand()

    def test_spotlight(self):
        # Test the spotlight function
        result = self.test_reminder.get_spotlight()
        self.assertIsInstance(result, str)
        self.assertIn("Vi har", result)
        self.assertIn("øl i spotlight", result)
