from django.contrib import admin
from .models import Event, EventChoice, EventChoiceOption, EventResponse


class EventChoiceOptionInline(admin.StackedInline):
	model = EventChoiceOption


@admin.register(EventChoice)
class EventChoiceAdmin(admin.ModelAdmin):
	inlines = [
		EventChoiceOptionInline,
	]


class EventResponseReadonlyInline(admin.TabularInline):
	model = EventResponse
	extra = 0

	def has_change_permission(self, request, obj=None):
		return False

	def has_delete_permission(self, request, obj=None):
		return False

	def has_add_permission(self, request, obj=None):
		return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	inlines = [
		EventResponseReadonlyInline,
	]


@admin.register(EventResponse)
class EventResponseAdmin(admin.ModelAdmin):
	pass
