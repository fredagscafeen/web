from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import StackedInline, TabularInline
from unfold.widgets import UnfoldAdminTextareaWidget

from bartenders.models import Bartender
from fredagscafeen.admin import CustomModelAdmin

from .models import CommonEvent, Event, EventChoice, EventChoiceOption, EventResponse


class EventChoiceInlineForm(forms.ModelForm):
    class Meta:
        model = EventChoice
        fields = ["name"]

    chosen_options = forms.CharField(
        label=_("Chosen options"), disabled=True, widget=UnfoldAdminTextareaWidget
    )

    def get_initial_for_field(self, field, fieldname):
        if fieldname == "chosen_options":
            if not self.instance.pk:
                return ""
            options = sorted(
                ((o.get_selected(), o.option) for o in self.instance.options.all()),
                reverse=True,
            )

            s = ""
            for selected, name in options:
                s += f"{selected}: {name}\n"

            return s

        return super().get_initial_for_field(field, fieldname)


class EventChoiceOptionInline(StackedInline):
    model = EventChoiceOption
    autocomplete_fields = ["event_choice"]


@admin.register(EventChoiceOption)
class EventChoiceOptionAdmin(CustomModelAdmin):
    autocomplete_fields = ["event_choice"]
    search_fields = ("option",)
    pass


@admin.register(EventChoice)
class EventChoiceAdmin(CustomModelAdmin):
    inlines = [
        EventChoiceOptionInline,
    ]
    autocomplete_fields = ["event"]
    search_fields = ("name",)


class EventResponseReadonlyInline(TabularInline):
    model = EventResponse
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class EventChoiceInline(TabularInline):
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
        widget=UnfoldAdminTextareaWidget,
    )

    def get_initial_for_field(self, field, fieldname):
        if fieldname == "default_may_attends":
            s = ""
            allowed = 0
            for b in Bartender.objects.all():
                if self.instance.may_attend_default(b):
                    s += f"- {b}\n"
                    allowed += 1
            bartenders = "bartenders"
            return f"{allowed} {bartenders}:\n" + s.strip()

        return super().get_initial_for_field(field, fieldname)


@admin.register(Event)
class EventAdmin(CustomModelAdmin):
    list_display = (
        "name",
        "year",
        "start_datetime",
        "end_datetime",
        "get_event_album_link",
    )
    filter_horizontal = (
        "bartender_whitelist",
        "bartender_blacklist",
    )
    form = EventAdminForm
    inlines = [
        EventChoiceInline,
        EventResponseReadonlyInline,
    ]
    autocomplete_fields = ["event_album"]
    search_fields = (
        "name",
        "year",
    )

    def get_event_album_link(self, event):
        album = event.event_album
        if album:
            kwargs = dict(year=album.year, album_slug=album.slug)
            html_string = '<a href="{}">' + album.title + "</a>"
            return format_html(html_string, reverse("album", kwargs=kwargs))

    get_event_album_link.short_description = _("Event Album")


@admin.register(EventResponse)
class EventResponseAdmin(CustomModelAdmin):
    autocomplete_fields = ["event", "bartender", "selected_options"]
    pass


@admin.register(CommonEvent)
class CommonEventAdmin(CustomModelAdmin):
    list_display = (
        "title",
        "date",
        "url",
    )
