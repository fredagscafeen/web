import datetime
import os
from unittest import skipUnless
from urllib.parse import urljoin

from django.conf import settings
from django.core import mail
from django.forms import model_to_dict
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bartenders.models import (
    Bartender,
    BartenderApplication,
    BoardMember,
    BoardMemberPeriod,
)


class BartenderApplicationTests(TestCase):
    def setUp(self):
        os.environ["RECAPTCHA_TESTING"] = "True"

    def tearDown(self):
        os.environ["RECAPTCHA_TESTING"] = "False"

    def test_accepting_application(self):
        d = dict(
            name="Abekat",
            username="abkat",
            email="kat@post.au.dk",
            studentNumber=20147510,
            phoneNumber=42345123,
        )
        ap = BartenderApplication.objects.create(
            **d, tshirt_size="L", study="Datalogi", study_year=1
        )
        ap.accept()

        # Test that a Bartender has been created with the correct data
        self.assertTrue(Bartender.objects.exists())
        self.assertDictEqual(
            d,
            {
                k: v
                for k, v in model_to_dict(Bartender.objects.first()).items()
                if k in d
            },
        )

        # Test that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [ap.email])

        link = urljoin(settings.SELF_URL, reverse("barplan"))
        self.assertIn(link, email.body)

    def test_sending_application(self):
        data = dict(
            name="Kat",
            username="Abe",
            email="abe@kat.dk",
            studentNumber=123123,
            phoneNumber=12312312,
            birthday=datetime.datetime(1993, 1, 1).date(),
            prefered_language="da",
            tshirt_size="L",
            study="Datalogi",
            study_year=1,
            info="Hkll",
        )

        data["g-recaptcha-response"] = "PASSED"
        response = self.client.post("/da/", data=data)
        # self.assertRedirects(response, "/")

        # Test that application was made
        self.assertTrue(BartenderApplication.objects.exists())
        # And mail was sent
        self.assertEqual(len(mail.outbox), 2)

    def test_invalid_application(self):
        data = dict(
            name="Morten",
            username="Olsen",
            email="cat@cs.au.no",
            studentNumber="NaN",
            phoneNumber=123,
            info="Kill dogs",
        )

        self.client.post("/da/", data=data)
        self.assertFalse(BartenderApplication.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_au_dk_email_application(self):
        data = dict(
            name="Kat",
            username="Abe",
            email="abe@post.au.dk",
            studentNumber=123123,
            phoneNumber=12312312,
            birthday=datetime.datetime(1993, 1, 1).date(),
            prefered_language="da",
            tshirt_size="L",
            study="Datalogi",
            study_year=1,
            info="Hkll",
        )

        self.client.post("/da/", data=data)
        self.assertFalse(BartenderApplication.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_board_member(self):
        bartender = Bartender.objects.create(
            name="Foo", username="foo", email="memes@memes.memes", studentNumber=123
        )

        self.assertFalse(bartender.isBoardMember)

        period = BoardMemberPeriod.objects.create(start_date=timezone.localdate())

        BoardMember.objects.create(
            bartender=bartender,
            period=period,
            title="Meme master",
            responsibilities="Memes",
        )

        self.assertTrue(bartender.isBoardMember)

    def test_board_member_periods(self):
        today = timezone.localdate()
        day = datetime.timedelta(days=1)

        p1 = BoardMemberPeriod.objects.create(start_date=today - 5 * day)
        p2 = BoardMemberPeriod.objects.create(start_date=today)
        p3 = BoardMemberPeriod.objects.create(start_date=today + 5 * day)

        self.assertEqual(p1.end_date, p2.start_date - day)
        self.assertEqual(p2.end_date, p3.start_date - day)
        self.assertEqual(p3.end_date, None)

        bartender = Bartender.objects.create(
            name="Bob", username="bob", email="bob@example.org"
        )

        boardmember = BoardMember.objects.create(
            bartender=bartender,
            period=p1,
            title="Formand",
            responsibilities="Ingenting",
        )

        self.assertFalse(bartender.isBoardMember)

        boardmember.period = p2
        boardmember.save()
        self.assertTrue(bartender.isBoardMember)

        boardmember.period = p3
        boardmember.save()
        self.assertFalse(bartender.isBoardMember)

        BoardMember.objects.create(
            bartender=bartender,
            period=p2,
            title="Næstformand",
            responsibilities="Løbesedler?",
        )

        self.assertTrue(bartender.isBoardMember)
