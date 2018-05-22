from tempfile import NamedTemporaryFile, TemporaryDirectory
import subprocess

from django.contrib import admin
from django import forms
from django.forms.widgets import TextInput
from django.http import FileResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from admin_views.admin import AdminViews

from easy_select2 import select2_modelform

from .models import BarTabUser, BarTabSnapshot, BarTabEntry, SumField


class BarTabUserAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'balance', 'hidden_from_tab')
	readonly_fields = ('balance',)
	search_fields = ('name', 'email')
	list_filter = ('hidden_from_tab',)


BarTabEntryForm = select2_modelform(BarTabEntry)


class BarTabEntryInline(admin.TabularInline):
	form = BarTabEntryForm
	model = BarTabEntry
	fields = ('raw_added', 'user', 'raw_used')
	extra = 1
	min_num = 1
	formfield_overrides = {
		SumField: {'widget': TextInput},
	}

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
			for _ in range(3):
				p = subprocess.run(['pdflatex', '-halt-on-error', '-jobname', 'bartab', filename], cwd=cwd, stdout=subprocess.PIPE)
				if p.returncode != 0:
					return HttpResponse(b'Got pdflatex error:\n\n' + p.stdout, content_type='text/plain')

			return FileResponse(open(cwd + '/bartab.pdf', 'rb'), content_type='application/pdf')


admin.site.register(BarTabUser, BarTabUserAdmin)
admin.site.register(BarTabSnapshot, BarTabSnapshotAdmin)
