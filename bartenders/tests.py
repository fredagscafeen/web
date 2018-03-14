import os
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from django.forms import model_to_dict
from django.test import TestCase
from django.core import mail
from rest_framework import status

from bartenders.models import BartenderApplication, Bartender


class BartenderApplicationTests(TestCase):
	def setUp(self):
		os.environ['RECAPTCHA_TESTING'] = 'True'

	def tearDown(self):
		os.environ['RECAPTCHA_TESTING'] = 'False'

	def test_accepting_application(self):
		ap = BartenderApplication.objects.create(name='Abekat', username='abkat', email='kat@post.au.dk', studentNumber=20147510, phoneNumber=42345123)
		ap.accept()

		# Test that a Bartender has been created with the correct data
		self.assertTrue(Bartender.objects.exists())
		b = model_to_dict(ap)
		b.update(isActiveBartender=True)
		b.pop('info')
		self.assertDictEqual(b, model_to_dict(Bartender.objects.first()))

		# Test that an email was sent
		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertEqual(email.to, [ap.email])

		link = urljoin(settings.SELF_URL, reverse('barplan'))
		self.assertIn(link, email.body)

	def test_sending_application(self):
		data = dict(
			name='Kat',
			username='Abe',
			email='abe@cs.au.dk',
			studentNumber=123123,
			phoneNumber=12312312,
			info='Hkll'
		)

		data['g-recaptcha-response'] = 'PASSED'
		response = self.client.post('/', data=data)
		self.assertRedirects(response, '/')

		# Test that application was made
		self.assertTrue(BartenderApplication.objects.exists())
		# And mail was sent
		self.assertEqual(len(mail.outbox), 1)

	def test_invalid_application(self):
		data = dict(
			name='Morten',
			username='Olsen',
			email='cat@cs.au.no',
			studentNumber='NaN',
			phoneNumber=123,
			info='Kill dogs'
		)

		response = self.client.post('/', data=data)
		self.assertFalse(BartenderApplication.objects.exists())
		self.assertEqual(len(mail.outbox), 0)
