from django import forms
from django.contrib import admin

from .models import Event, EventChoice, EventChoiceOption, EventResponse


class EventChoiceInlineForm(forms.ModelForm):
    class Meta:
        model = EventChoice
        fields = ["name"]

    chosen_options = forms.CharField(
        label="Chosen options", disabled=True, widget=forms.Textarea
    )

    def get_initial_for_field(self, field, fieldname):
        if fieldname == "chosen_options":
            options = sorted(
                ((o.get_selected(), o.option) for o in self.instance.options.all()),
                reverse=True,
            )

            s = ""
            for selected, name in options:
                s += f"{selected}: {name}\n"

            return s

        return super().get_initial_for_field(field, fieldname)


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


class EventChoiceInline(admin.TabularInline):
    model = EventChoice
    show_change_link = True
    form = EventChoiceInlineForm


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    inlines = [
        EventChoiceInline,
        EventResponseReadonlyInline,
    ]


@admin.register(EventResponse)
class EventResponseAdmin(admin.ModelAdmin):
    pass
