from collections import namedtuple
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.db import models

SumValue = namedtuple("SumValue", ["string", "value"])


def parse_sum(s):
    if s.strip() == "":
        return SumValue("", 0)

    s = s.replace(",", ".")
    value = 0
    for d in map(Decimal, s.split("+")):
        if -d.as_tuple().exponent > 2:
            raise ValueError
        value += d

    return SumValue(s, value)


class SumFormField(forms.CharField):
    def clean(self, value):
        try:
            return parse_sum(value)
        except (ValueError, InvalidOperation):
            raise ValidationError("Invalid sum")

    def prepare_value(self, value):
        if isinstance(value, str) or value == None:
            return value
        return value.string


class SumField(models.TextField):
    def from_db_value(self, value, expression, connection):
        if value == None:
            return None
        return parse_sum(value)

    def to_python(self, value):
        if isinstance(value, SumValue) or value == None:
            return value
        return parse_sum(value)

    def get_prep_value(self, value):
        if value == "" or value == None:
            return None

        if isinstance(value, str):
            return value

        return value.string

    def value_to_string(self, obj):
        """Allows serialization of SumFields (dumpdata/loaddata)"""
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": SumFormField, **kwargs})
