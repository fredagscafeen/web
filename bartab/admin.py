import subprocess
from tempfile import NamedTemporaryFile, TemporaryDirectory

from admin_views.admin import AdminViews
from django.contrib import admin
from django.forms.widgets import TextInput
from django.http import FileResponse, HttpResponse
from django.template.loader import render_to_string
from easy_select2 import Select2

from .models import BarTabUser, BarTabSnapshot, BarTabEntry, SumField


class BarTabUserAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'balance', 'hidden_from_tab')
	readonly_fields = ('balance',)
	search_fields = ('name', 'email')
	list_filter = ('hidden_from_tab',)


class BarTabEntryInline(admin.TabularInline):
	model = BarTabEntry
	fields = ('raw_added', 'user', 'raw_used')
	extra = 1
	min_num = 1
	formfield_overrides = {
		SumField: {'widget': TextInput},
	}

	def get_queryset(self, request):
		""" Select related prevents 2*N queries when calling entry.__str__ in each form """
		return super().get_queryset(request).select_related('user', 'snapshot')

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		""" Override user field to cache choices instead of making N queries for BarTabUsers """

		field = super().formfield_for_foreignkey(db_field, request, **kwargs)
		if db_field.name == 'user':
			# Here we exploit that choices is a property
			# On the RHS the original choices function is called which creates a generator that yields choice-tuples from the queryset
			# The output of the generator is stored in a list to spare each render of the field of evaluating the queryset
			field.choices = list(field.choices)
			field.widget = Select2()

		return field

	def formfield_for_dbfield(self, db_field, **kwargs):
		field = super().formfield_for_dbfield(db_field, **kwargs)
		if db_field.name == 'raw_used':
			field.widget.attrs['size'] = '50'
		return field


class BarTabSnapshotAdmin(AdminViews):
	change_form_template = 'admin/bartabsnapshot.html'
	readonly_fields = ('timestamp',)
	inlines = [
		BarTabEntryInline,
	]
	admin_views = (
		('Generate bartab', 'generate_bartab'),
	)

	def generate_bartab(self, request):
		with NamedTemporaryFile('w', suffix='-bartab.tex', delete=False) as f:
			filename = f.name

			tab_parts = (([], 'Aktive'), ([], 'Inaktive'))
			for user in BarTabUser.objects.exclude(hidden_from_tab=True):
				tab_parts[not user.is_active][0].append(user)

			latex = render_to_string('bartab/bartab.tex', {
				'tab_parts': tab_parts,
				'pizza_lines': range(33),
			}, request)
			f.write(latex)

		with TemporaryDirectory() as cwd:
			p = subprocess.run(['latexmk', '-halt-on-error', '-pdf', '-jobname=bartab', filename], cwd=cwd, stdout=subprocess.PIPE)
			if p.returncode != 0:
				error_text = f'''==== Got an error from latexmk ====

== LaTeX source ==

{latex}

== latexmk output ==

{str(p.stdout, 'utf-8')}'''
				return HttpResponse(error_text, content_type='text/plain')

			return FileResponse(open(cwd + '/bartab.pdf', 'rb'), content_type='application/pdf')


admin.site.register(BarTabUser, BarTabUserAdmin)
admin.site.register(BarTabSnapshot, BarTabSnapshotAdmin)
