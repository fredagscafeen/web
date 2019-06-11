from django.db import models
from django.utils import timezone
from bartenders.models import Bartender


class EventChoice(models.Model):
	name = models.CharField(max_length=255)

	def __str__(self):
		return self.name


class EventChoiceOption(models.Model):
	class Meta:
		unique_together = ('event_choice', 'option')

	event_choice = models.ForeignKey(EventChoice, on_delete=models.CASCADE, related_name='options')
	option = models.CharField(max_length=255)

	def __str__(self):
		return self.option


class Event(models.Model):
	class Meta:
		ordering = ('-start_datetime',)

	name = models.CharField(max_length=255)
	location = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	start_datetime = models.DateTimeField()
	end_datetime = models.DateTimeField()
	response_deadline = models.DateTimeField()
	event_choices = models.ManyToManyField(EventChoice)

	def __str__(self):
		return self.name

	def deadline_exceeded(self):
		return timezone.now() > self.response_deadline
	

class EventResponse(models.Model):
	class Meta:
		unique_together = ('event', 'bartender')

	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='responses')
	bartender = models.ForeignKey(Bartender, on_delete=models.CASCADE)
	attending = models.BooleanField()
	choices = models.ManyToManyField(EventChoiceOption)

	def __str__(self):
		return f'{self.event}, {self.bartender}: {self.attending}'

	def _assert_event_has_event_choice(self, event_choice):
		assert self.event.event_choices.filter(id=event_choice.id).exists()
	
	def clear_option(self, event_choice):
		self._assert_event_has_event_choice(event_choice)
		self.choices.remove(*self.choices.filter(event_choice=event_choice))

	def set_option(self, option):
		self.clear_option(option.event_choice)
		self.choices.add(option)
	
	def get_option(self, event_choice):
		self._assert_event_has_event_choice(event_choice)

		try:
			return self.choices.get(event_choice=event_choice)
		except EventChoiceOption.DoesNotExist:
			return None
