from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bartenders.models import Bartender

from .models import Event, EventChoice, EventChoiceOption, EventResponse


class EventChoiceInlineForm(forms.ModelForm):
    class Meta:
        model = EventChoice
        fields = ["name"]

    chosen_options = forms.CharField(
        label=_("Chosen options"), disabled=True, widget=forms.Textarea
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


class EventAdminForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = "__all__"

    default_may_attends = forms.CharField(
        label=_("Default allowed attendees"),
        help_text=_("Can be overwritten using the whitelist and blacklist above."),
        disabled=True,
        widget=forms.Textarea,
    )

    def get_initial_for_field(self, field, fieldname):
        if fieldname == "default_may_attends":
            s = ""
            allowed = 0
            for b in Bartender.objects.all():
                if self.instance.may_attend_default(b):
                    s += f"- {b}\n"
                    allowed += 1
            bartenders = _("bartenders")
            return f"{allowed} {bartenders}:\n" + s.strip()

        return super().get_initial_for_field(field, fieldname)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    inlines = [
        EventChoiceInline,
        EventResponseReadonlyInline,
    ]


@admin.register(EventResponse)
class EventResponseAdmin(admin.ModelAdmin):
    pass
