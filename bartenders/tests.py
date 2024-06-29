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

from .mailman2 import Mailman


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
            email="abe@cs.au.dk",
            studentNumber=123123,
            phoneNumber=12312312,
            tshirt_size="L",
            study="Datalogi",
            study_year=1,
            info="Hkll",
        )

        data["g-recaptcha-response"] = "PASSED"
        response = self.client.post("/", data=data)
        # self.assertRedirects(response, "/")

        # Test that application was made
        self.assertTrue(BartenderApplication.objects.exists())
        # And mail was sent
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_application(self):
        data = dict(
            name="Morten",
            username="Olsen",
            email="cat@cs.au.no",
            studentNumber="NaN",
            phoneNumber=123,
            info="Kill dogs",
        )

        self.client.post("/", data=data)
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

    @skipUnless(
        getattr(settings, "MAILMAN_ALL_PASSWORD", None),
        "Mailman password for all list not set",
    )
    def test_mailman_all_list_members(self):
        mailman = Mailman(
            settings.MAILMAN_URL_BASE,
            settings.MAILMAN_ALL_LIST,
            settings.MAILMAN_ALL_PASSWORD,
        )

        subscribers = mailman.get_subscribers()
        self.assertFalse(len(subscribers) == 0)

    @skipUnless(
        getattr(settings, "MAILMAN_BEST_PASSWORD", None),
        "Mailman password for best list not set",
    )
    def test_mailman_best_list_members(self):
        mailman = Mailman(
            settings.MAILMAN_URL_BASE,
            settings.MAILMAN_BEST_LIST,
            settings.MAILMAN_BEST_PASSWORD,
        )

        subscribers = mailman.get_subscribers()
        self.assertFalse(len(subscribers) == 0)
