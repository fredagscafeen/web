from django.contrib import admin
from django import forms
from django.forms.widgets import TextInput

from .models import BarTabUser, BarTabSnapshot, BarTabEntry, SumField


class BarTabUserAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'balance', 'hidden_from_tab')
	readonly_fields = ('balance',)
	search_fields = ('name', 'email')
	list_filter = ('hidden_from_tab',)


class BarTabEntryInlineFormSet(forms.models.BaseInlineFormSet):
	def clean(self):
		super().clean()
		for form in self.forms:
			pass


class BarTabEntryInline(admin.TabularInline):
	model = BarTabEntry
	fields = ('raw_added', 'user', 'raw_used')
	formset = BarTabEntryInlineFormSet
	formfield_overrides = {
		SumField: {'widget': TextInput},
	}

	def formfield_for_dbfield(self, db_field, **kwargs):
		field = super().formfield_for_dbfield(db_field, **kwargs)
		if db_field.name == 'raw_used':
			field.widget.attrs['size'] = '50'
		return field


class BarTabSnapshotAdmin(admin.ModelAdmin):
	readonly_fields = ('timestamp',)
	inlines = [
			BarTabEntryInline,
			]


	admin.site.register(BarTabUser, BarTabUserAdmin)
admin.site.register(BarTabSnapshot, BarTabSnapshotAdmin)
