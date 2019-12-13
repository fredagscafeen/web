from django.contrib import admin
from django.db import models
from django.forms.widgets import Select

from .models import Printer


class PrinterSelect(Select):
	def __init__(self, *args, **kwargs):
		kwargs['choices'] = Printer.PrinterChoiceIter()
		super().__init__(*args, **kwargs)


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': PrinterSelect},
	}
