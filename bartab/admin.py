from tempfile import NamedTemporaryFile, TemporaryDirectory
import subprocess

from django.contrib import admin
from django import forms
from django.forms.widgets import TextInput
from django.http import FileResponse, HttpResponse
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
			f.write(r'''
\documentclass[a4paper,oneside,article,11pt,english]{memoir}
\usepackage[margin=1cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage{microtype}
\usepackage{longtable}
\usepackage{tabu}
\usepackage[breakall]{truncate}
\usepackage{pdflscape}

\renewcommand\TruncateMarker{}

\pagestyle{empty}

\begin{document}

\large

\begin{landscape}
			''')

			tab_lines = [[], []]
			for user in BarTabUser.objects.exclude(hidden_from_tab=True):
				credit_hold = r'\textbf{KREDITSTOP}' if user.has_credit_hold else ''
				line = ''
				for field in [user.name, user.email or '', r'\hfill' + user.balance_str, credit_hold]:
					line += rf'& \truncate{{\linewidth}}{{ {field} }}'
				tab_lines[user.is_active].append(line + r'\\ \hline')


			for active, active_name in [(True, 'Aktive'), (False, 'Inaktive')]:
				if not active:
					f.write(r'\newpage')

				f.write(r'''
\section*{''' + active_name + r''' kunder \hfill ''' + str(timezone.now().date()) +  r'''}

\begin{longtabu} to \linewidth{| X[1, l] | X[4, l] | X[2, l] | X[1, r] | X[10, l] |}
\hline
\textbf{Indsat} & \textbf{Navn} & \textbf{Email} & \textbf{Saldo} & \textbf{Køb} \hfill \\ \hline
			''')
				for line in tab_lines[active]:
					f.write(line + '\n')

				f.write(r'\end{longtabu}')

			f.write(r'\end{landscape}')

			f.write(r'''
			\LARGE
			\section*{Pizzabestilling}
			\begin{tabu} to \linewidth{| X[1] | X[12] | X[2] |}
			\hline
			\textbf{Nr.} & \textbf{Navn} & \textbf{Betalt} \\ \hline
			''')

			for _ in range(33):
				f.write(r'& & \\ \hline')

			f.write(r'\end{tabu}')


			f.write(r'\end{document}')


		with TemporaryDirectory() as cwd:
			for _ in range(3):
				p = subprocess.run(['pdflatex', '-halt-on-error', '-jobname', 'bartab', filename], cwd=cwd, stdout=subprocess.PIPE)
				if p.returncode != 0:
					return HttpResponse(b'Got pdflatex error:\n\n' + p.stdout, content_type='text/plain')

			return FileResponse(open(cwd + '/bartab.pdf', 'rb'), content_type='application/pdf')


admin.site.register(BarTabUser, BarTabUserAdmin)
admin.site.register(BarTabSnapshot, BarTabSnapshotAdmin)
