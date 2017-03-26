from urllib.parse import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import model_to_dict
from django.test import TestCase
from django.core import mail

from bartenders.models import BartenderApplication, Bartender


class BartenderApplicationTests(TestCase):
	def test_accepting_application(self):
		ap = BartenderApplication.objects.create(name='Abekat', username='abkat', email='kat@post.au.dk', studentNumber=20147510, phoneNumber=42345123)
		ap.accept()

		# Test that a Bartender has been created with the correct data
		self.assertTrue(Bartender.objects.exists())
		b = model_to_dict(ap)
		b.update(isActiveBartender=True)
		b.update(isBoardMember=False)
		self.assertDictEqual(b, model_to_dict(Bartender.objects.first()))

		# Test that an email was sent
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, [ap.email])

		link = urljoin(settings.SELF_URL, reverse('barplan'))
		self.assertIn(link, mail.outbox[0].body)
