from django.test import TestCase
from django.utils import timezone
from .models import EventChoice, EventChoiceOption, Event, EventResponse
from bartenders.models import Bartender


class TestEvents(TestCase):
	def test_event(self):
		event_choice = EventChoice.objects.create(name='Related')
		event_choice_unrelated = EventChoice.objects.create(name='Unrelated')

		option_a = EventChoiceOption.objects.create(event_choice=event_choice, option='A')
		option_b = EventChoiceOption.objects.create(event_choice=event_choice, option='B')

		option_unrelated = EventChoiceOption.objects.create(event_choice=event_choice_unrelated, option='C')

		event = Event.objects.create(name='Event',
				                     description='...',
									 start_datetime=timezone.now(),
									 end_datetime=timezone.now(),
									 response_deadline=timezone.now())
		
		event.event_choices.add(event_choice)

		bartender = Bartender.objects.create(name='Foo',
				                             username='foo')

		response = EventResponse.objects.create(event=event,
				                                bartender=bartender,
												attending=True)
		
		self.assertEqual(response.get_option(event_choice), None)
		response.set_option(option_a)
		self.assertEqual(response.get_option(event_choice), option_a)
		response.set_option(option_b)
		self.assertEqual(response.get_option(event_choice), option_b)
		response.clear_option(event_choice)
		self.assertEqual(response.get_option(event_choice), None)

		with self.assertRaises(Exception):
			response.clear_option(event_choice_unrelated)

		with self.assertRaises(Exception):
			response.set_option(option_unrelated)

		with self.assertRaises(Exception):
			response.get_option(event_choice_unrelated)
