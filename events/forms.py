from django import forms
from django.core.exceptions import ValidationError
from .models import EventResponse


class EventResponseForm(forms.Form):
	ATTENDING_CHOICES = (
		(None, '---------'),
		(True, 'Deltager'),
		(False, 'Deltager ikke'),
	)


	def _to_bool(self, s):
		if s == 'False':
			return False
		elif s == 'True':
			return True
		else:
			return None


	def __init__(self, *args, event, bartender, **kwargs):
		super().__init__(*args, **kwargs)

		self.event = event
		self.bartender = bartender

		try:
			event_response = EventResponse.objects.get(event=event, bartender=bartender)
		except EventResponse.DoesNotExist:
			event_response = None

		attending_choices = self.ATTENDING_CHOICES
		if event_response:
			attending_choices = self.ATTENDING_CHOICES[1:]

		self.fields['attending'] = forms.TypedChoiceField(label='Deltager',
				                                          choices=attending_choices,
														  coerce=self._to_bool)
		if event_response:
			self.fields['attending'].initial = event_response.attending

		for choice in event.event_choices.all():
			field = forms.ModelChoiceField(label=choice.name, queryset=choice.options, required=False)
			if event_response:
				field.initial = event_response.get_option(choice)

			self.fields[f'choice_{choice.name}'] = field


		if event.deadline_exceeded():
			for field in self.fields.values():
				field.disabled = True


	def clean(self):
		super().clean()
		if self.cleaned_data['attending']:
			try:
				response = EventResponse.objects.get(
					event=self.event,
					bartender=self.bartender,
				)
			except EventResponse.DoesNotExist:
				response = None
			for choice in self.event.event_choices.all():
				if not self.cleaned_data.get(f'choice_{choice.name}'):
					raise ValidationError('Du skal udfylde alle felter, når du deltager')

				option = self.cleaned_data[f'choice_{choice.name}']
				if response and response.can_set_option(option):
					continue

				if not response and EventResponse.can_add_option(self.event, option):
					continue

				raise ValidationError(f'Der er for mange der har valgt {option.option}. Vælg noget andet.')


	def save(self):
		attending = self.cleaned_data['attending']
		response, _ = EventResponse.objects.update_or_create(
			event=self.event,
			bartender=self.bartender,
			defaults={
				'attending': attending,
			})

		if attending:
			response.choices.clear()
			for choice in self.event.event_choices.all():
				response.set_option(self.cleaned_data[f'choice_{choice.name}'])

		return response
