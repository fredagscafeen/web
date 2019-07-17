from django.db import models
from django.utils import timezone
from bartenders.models import Bartender


class EventChoice(models.Model):
	name = models.CharField(max_length=255)
	event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='event_choices')

	def __str__(self):
		return f'{self.event}: {self.name}'


class EventChoiceOption(models.Model):
	class Meta:
		unique_together = ('event_choice', 'option')

	event_choice = models.ForeignKey(EventChoice, on_delete=models.CASCADE, related_name='options')
	option = models.CharField(max_length=255)
	max_selected = models.PositiveIntegerField(blank=True, null=True)

	def __str__(self):
		selected = self.get_selected()
		if self.max_selected:
			return f'{self.option} ({selected}, max {self.max_selected})'
		return f'{self.option} ({selected})'

	def get_selected(self):
		return EventResponse.objects.filter(selected_options=self).count()

	def can_more_choose(self):
		return self.max_selected == None or self.get_selected() < self.max_selected

	def can_bartender_choose(self, bartender):
		if self.can_more_choose():
			return True

		try:
			response = EventResponse.objects.get(event=self.event_choice.event, bartender=bartender)
			return response.get_option(self.event_choice) == self
		except EventResponse.DoesNotExist:
			return False


class Event(models.Model):
	class Meta:
		ordering = ('-start_datetime',)

	name = models.CharField(max_length=255)
	location = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	start_datetime = models.DateTimeField()
	end_datetime = models.DateTimeField()
	response_deadline = models.DateTimeField()

	def __str__(self):
		return self.name

	def deadline_exceeded(self):
		return timezone.now() > self.response_deadline
	
	def attending_count(self):
		return sum(r.attending for r in self.responses.all())

	def sorted_responses(self):
		return sorted(self.responses.all(), key=lambda r: r.bartender.name)

	def sorted_choices(self):
		return self.event_choices.order_by('id')


class EventResponse(models.Model):
	class Meta:
		unique_together = ('event', 'bartender')

	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='responses')
	bartender = models.ForeignKey(Bartender, on_delete=models.CASCADE)
	attending = models.BooleanField()
	selected_options = models.ManyToManyField(EventChoiceOption)

	def __str__(self):
		return f'{self.event}, {self.bartender}: {self.attending}'

	def _assert_event_has_event_choice(self, event_choice):
		assert self.event.event_choices.filter(id=event_choice.id).exists()
	
	def clear_option(self, event_choice):
		self._assert_event_has_event_choice(event_choice)
		self.selected_options.remove(*self.selected_options.filter(event_choice=event_choice))

	def set_option(self, option):
		assert self.can_set_option(option)
		self.clear_option(option.event_choice)
		self.selected_options.add(option)
	
	def can_set_option(self, option):
		return option.can_bartender_choose(self.bartender)

	def get_option(self, event_choice):
		self._assert_event_has_event_choice(event_choice)

		try:
			return self.selected_options.get(event_choice=event_choice)
		except EventChoiceOption.DoesNotExist:
			return None

	def get_sorted_options(self):
		return sorted(self.selected_options.all(), key=lambda o: o.event_choice.id)
