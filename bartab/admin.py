from tempfile import TemporaryDirectory

from admin_views.admin import AdminViews
from django.contrib import admin
from django.forms.widgets import TextInput
from django.http import FileResponse, HttpResponse

from .models import BarTabUser, BarTabSnapshot, BarTabEntry, SumField
from .latex import generate_bartab, LatexError


class BarTabEntryReadonlyInline(admin.TabularInline):
	model = BarTabEntry
	fields = ('added', 'used')
	readonly_fields = ('added', 'used')
	can_delete = False
	extra = 0

	def has_add_permission(self, request):
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
	change_form_template = 'admin/bartabsnapshot.html'
	readonly_fields = ('last_updated',)
	inlines = [
		BarTabEntryInline,
	]
	admin_views = (
		('Generate bartab', 'generate_bartab'),
	)

	def generate_bartab(self, request):
		with TemporaryDirectory() as d:
			try:
				f = generate_bartab(d)
				return FileResponse(f, content_type='application/pdf')
			except LatexError as e:
				with open(f'{d}/bartab.tex') as f:
					source = f.read()

				error_text = f'''==== Got an error from latexmk ====

== latexmk output ==

{e.message}

== LaTeX source ==

{source}'''
				return HttpResponse(error_text, content_type='text/plain')

admin.site.register(BarTabUser, BarTabUserAdmin)
admin.site.register(BarTabSnapshot, BarTabSnapshotAdmin)
