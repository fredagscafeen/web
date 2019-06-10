from django.contrib import admin
from .models import Event, EventChoice, EventChoiceOption, EventResponse


class EventChoiceOptionInline(admin.StackedInline):
	model = EventChoiceOption


@admin.register(EventChoice)
class EventChoiceAdmin(admin.ModelAdmin):
	inlines = [
		EventChoiceOptionInline,
	]
	pass


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	pass


@admin.register(EventResponse)
class EventResponseAdmin(admin.ModelAdmin):
	pass

