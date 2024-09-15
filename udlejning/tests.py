import datetime
import os

import pytz
from django.core import mail
from django.test import TestCase

from udlejning.models import Udlejning, UdlejningApplication


# Create your tests here.
class UdlejningApplicationTests(TestCase):
    def setUp(self):
        os.environ["RECAPTCHA_TESTING"] = "True"

    def tearDown(self):
        os.environ["RECAPTCHA_TESTING"] = "False"

    def test_accepting_application(self):
        d = dict(
            dateFrom=datetime.datetime(2024, 9, 16, 16, 0, tzinfo=pytz.UTC),
            dateTo=None,
            whoReserved="Abekat",
            contactEmail="kat@mail.dk",
            contactPhone=42345123,
            whoPays="AU",
            paymentType="EAN",
            EANnumber=1234567890123,
            where="Nygaard-02",
            expectedConsummation="Alt for meget",
            comments="Igen kommentar",
        )
        ap = UdlejningApplication.objects.create(**d)
        ap.accept()

        # Test that an application has been created with the correct data
        self.assertTrue(Udlejning.objects.exists())

    def test_sending_application(self):
        data = dict(
            dateFrom=datetime.datetime(2024, 9, 16, 16, 0, tzinfo=pytz.UTC),
            dateTo=datetime.datetime(2024, 9, 16, 22, 0, tzinfo=pytz.UTC),
            whoReserved="Abekat",
            contactEmail="kat@mail.dk",
            contactPhone=42345123,
            whoPays="AU",
            paymentType="card",
            where="Nygaard-02",
            expectedConsummation="Alt for meget",
            comments="Igen kommentar",
        )

        data["g-recaptcha-response"] = "PASSED"
        response = self.client.post("/da/udlejning/#rentingform", data=data)
        # self.assertRedirects(response, "/da/udlejning/")

        # Test that application was made
        self.assertTrue(UdlejningApplication.objects.exists())
        # And mail was sent
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_application(self):
        # Missing payment info
        data = dict(
            dateFrom=datetime.datetime(2024, 9, 16, 16, 0, tzinfo=pytz.UTC),
            dateTo=datetime.datetime(2024, 9, 16, 22, 0, tzinfo=pytz.UTC),
            whoReserved="Abekat",
            contactEmail="kat@mail.dk",
            contactPhone=42345123,
            where="Nygaard-02",
            expectedConsummation="Alt for meget",
            comments="Igen kommentar",
        )

        self.client.post("/da/udlejning/", data=data)
        self.assertFalse(UdlejningApplication.objects.exists())
        self.assertEqual(len(mail.outbox), 0)
