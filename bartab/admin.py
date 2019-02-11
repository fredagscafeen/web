from tempfile import TemporaryDirectory
from collections import Counter
import shutil

from admin_views.admin import AdminViews
from django.contrib import admin
from django.db import models
from django.forms.widgets import TextInput, Select
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.conf import settings

from .forms import ConsumptionForm, PrintForm
from .models import BarTabUser, BarTabSnapshot, BarTabEntry, SumField, Printer
from .latex import generate_bartab, LatexError


class BarTabEntryReadonlyInline(admin.TabularInline):
	model = BarTabEntry
	fields = ('added', 'used')
	readonly_fields = ('added', 'used')
	extra = 0

	def has_change_permission(self, request, obj=None):
		return False

	def has_delete_permission(self, request, obj=None):
		return False

	def has_add_permission(self, request, obj=None):
		return False


class BarTabUserAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'balance', 'hidden_from_tab')
	readonly_fields = ('balance',)
	search_fields = ('name', 'email')
	list_filter = ('hidden_from_tab',)
	inlines = [
		BarTabEntryReadonlyInline,
	]


class BarTabEntryInline(admin.TabularInline):
	model = BarTabEntry
	fields = ('added_cash', 'raw_added', 'user', 'raw_used')
	extra = 1
	min_num = 1
	formfield_overrides = {
		SumField: {'widget': TextInput},
	}
	autocomplete_fields = ['user']

	def get_queryset(self, request):
		""" Select related prevents 2*N queries when calling entry.__str__ in each form """
		return super().get_queryset(request).select_related('user', 'snapshot')

	def formfield_for_dbfield(self, db_field, **kwargs):
		field = super().formfield_for_dbfield(db_field, **kwargs)
		if db_field.name == 'raw_used':
			field.widget.attrs['size'] = '50'
		return field


class BarTabSnapshotAdmin(AdminViews):
	list_display = ('date', 'entry_count', 'total_added', 'total_used')
	change_form_template = 'admin/bartabsnapshot.html'
	readonly_fields = ('last_updated', 'total_added', 'total_used')
	inlines = [
		BarTabEntryInline,
	]
	admin_views = (
		('Generate bartab', 'generate_bartab'),
		('Count consumption', 'count_consumption'),
	)

	def entry_count(self, obj):
		return obj.entries.count()

	def generate_bartab(self, request):
		PDF_PATH = f'{settings.MEDIA_ROOT}/bartab.pdf'

		form = PrintForm()

		if request.method == 'POST':
			form = PrintForm(request.POST)
			if form.is_valid():
				printer = form.cleaned_data['printer']
				job_id = printer.print(PDF_PATH)

				context = dict(
					# Include common variables for rendering the admin template.
					self.admin_site.each_context(request),
					# Anything else you want in the context...
					printer_name=printer.name,
					job_id=job_id,
				)
				return TemplateResponse(request, 'bartab/print_status.html', context)


		if request.method == 'GET':
			with TemporaryDirectory() as d:
				try:
					fname = generate_bartab(d)
					shutil.copy(fname, PDF_PATH)
				except LatexError as e:
					with open(f'{d}/bartab.tex') as f:
						source = f.read()

					error_text = f'''==== Got an error from latexmk ====

	== latexmk output ==

	{e.message}

	== LaTeX source ==

	{source}'''
					return HttpResponse(error_text, content_type='text/plain')

		context = dict(
			# Include common variables for rendering the admin template.
			self.admin_site.each_context(request),
			# Anything else you want in the context...
			form=form,
			bartab_url=f'{settings.MEDIA_URL}/bartab.pdf',
		)
		return TemplateResponse(request, 'bartab/bartab.html', context)


	def count_consumption(self, request):
		result = None

		if request.method == 'POST':
			form = ConsumptionForm(request.POST)
			if form.is_valid():
				counter = Counter()

				start = form.cleaned_data['start_snapshot']
				end = form.cleaned_data['end_snapshot']

				for snapshot in BarTabSnapshot.objects.all():
					if start.datetime <= snapshot.datetime <= end.datetime:
						for entry in snapshot.entries.all():
							counter[entry.user] += entry.used

				result = counter.most_common()
		else:
			form = ConsumptionForm()

		context = dict(
			# Include common variables for rendering the admin template.
			self.admin_site.each_context(request),
			# Anything else you want in the context...
			form=form,
			result=result,
		)
		return TemplateResponse(request, 'bartab/consumption.html', context)


class PrinterSelect(Select):
	def __init__(self, *args, **kwargs):
		kwargs['choices'] = Printer.PrinterChoiceIter()
		super().__init__(*args, **kwargs)


class PrinterAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': PrinterSelect},
	}


admin.site.register(BarTabUser, BarTabUserAdmin)
admin.site.register(BarTabSnapshot, BarTabSnapshotAdmin)
admin.site.register(Printer, PrinterAdmin)
