from decimal import Decimal, InvalidOperation
from collections import namedtuple

from django import forms
from django.core.exceptions import ValidationError


SumValue = namedtuple('SumValue', ['string', 'value'])


class SumField(forms.CharField):
	@staticmethod
	def _parse_sum(s):
		s = s.replace(',', '.')
		value = 0
		for d in map(Decimal, s.split('+')):
			if -d.as_tuple().exponent > 2:
				raise ValueError
			value += d

		return SumValue(s, value)

	def clean(self, value):
		try:
			self._parse_sum(value)
			return value
		except (ValueError, InvalidOperation):
			raise ValidationError('Invalid sum')

	def prepare_value(self, value):
		if isinstance(value, str) or value == None:
			return value
		return value.string
