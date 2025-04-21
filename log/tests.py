from django.test import TestCase
from django.utils import timezone

from bartenders.models import Bartender, BartenderShift

from .models import LogBase, LogEntry


class LogBaseTests(TestCase):
    def setUp(self):
        foo = Bartender.objects.create(
            name="Foo", username="foo", email="foo@fredagscafeen.dk", studentNumber=123
        )
        bar = Bartender.objects.create(
            name="Bar", username="bar", email="bar@fredagscafeen.dk", studentNumber=124
        )
        self.log_base = LogBase.objects.create(
            manager=foo,
            licensee=bar,
            purpose="Test Purpose",
            representative="Anders And (and@cs.au.dk)",
            type="Fredagsbar",
            guests="10 - 150",
            loan_agreement=bar,
        )

    def test_log_base_creation(self):
        self.assertIsInstance(self.log_base, LogBase)
        self.assertEqual(self.log_base.manager.name, "Foo")
        self.assertEqual(self.log_base.licensee.name, "Bar")
        self.assertEqual(self.log_base.purpose, "Test Purpose")
        self.assertEqual(self.log_base.representative, "Anders And (and@cs.au.dk)")
        self.assertEqual(self.log_base.type, "Fredagsbar")
        self.assertEqual(self.log_base.guests, "10 - 150")

    def test_str_method(self):
        expected_str = f"{self.log_base.created_at.date()}: Bestyrer: {self.log_base.manager}, Bevillingshaver: {self.log_base.licensee}"
        self.assertEqual(str(self.log_base), expected_str)


class LogEntryTests(TestCase):
    def setUp(self):
        foo = Bartender.objects.create(
            name="Foo", username="foo", email="foo@fredagscafeen.dk", studentNumber=123
        )
        bar = Bartender.objects.create(
            name="Bar", username="bar", email="bar@fredagscafeen.dk", studentNumber=124
        )
        self.log_base = LogBase.objects.create(
            manager=foo,
            licensee=bar,
            purpose="Test Purpose",
            representative="Anders And (and@cs.au.dk)",
            type="Fredagsbar",
            guests="10 - 150",
            loan_agreement=bar,
        )
        bartender_shift = BartenderShift.objects.create(
            responsible=foo,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timezone.timedelta(hours=4),
        )
        self.log_entry = LogEntry.objects.create(
            template=self.log_base,
            bartender_shift=bartender_shift,
            location="Test Location",
            description="Test Description",
        )

    def test_log_entry_creation(self):
        self.assertIsInstance(self.log_entry, LogEntry)
        self.assertEqual(self.log_entry.template, self.log_base)
        self.assertEqual(self.log_entry.location, "Test Location")
        self.assertEqual(self.log_entry.short_description, "Test Description")

    def test_str_method(self):
        expected_str = f"{self.log_entry.bartender_shift.start_datetime.date()}: {self.log_entry.bartender_shift.responsible.name}"
        self.assertEqual(str(self.log_entry), expected_str)
