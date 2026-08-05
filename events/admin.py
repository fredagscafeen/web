from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import StackedInline, TabularInline, mark_safe
from unfold.widgets import UnfoldAdminTextareaWidget

from bartenders.models import Bartender
from fredagscafeen.admin import CustomModelAdmin

from .models import Event, EventChoice, EventChoiceOption, EventLink, EventResponse


class EventLinkInlineForm(forms.ModelForm):
    class Meta:
        model = EventLink
        fields = ["type", "title", "url"]

    def get_initial_for_field(self, field, field_name):
        if field_name == "title":
            return self.instance.get_title()

        return super().get_initial_for_field(field, field_name)


class EventChoiceOptionInline(StackedInline):
    model = EventChoiceOption
    extra = 1
    autocomplete_fields = ["event_choice"]

    fields = [
        ("option", "max_selected"),
    ]


@admin.register(EventChoiceOption)
class EventChoiceOptionAdmin(CustomModelAdmin):
    autocomplete_fields = ["event_choice"]
    search_fields = ("option",)

    # Disable access to the EventChoiceOption model in the admin site
    def has_module_permission(self, request):
        return False


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
    tab = True

    autocomplete_fields = ["event", "bartender"]

    readonly_fields = [
        "attending",
        "bartender",
        "display_selected_options",
    ]

    fields = [
        "attending",
        "bartender",
        "display_selected_options",
    ]

    @admin.display(description=_("Selected options"))
    def display_selected_options(self, obj):
        if not obj or not obj.pk:
            return ""

        queryset = obj.selected_options.all()
        if not queryset.exists():
            return "-"

        return mark_safe(
            "<br>".join(
                f"<span class='font-semibold'>{o.event_choice.name}:</span> {o.option}"
                for o in queryset
            )
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class EventChoiceInline(TabularInline):
    model = EventChoice
    show_change_link = True
    tab = True
    extra = 0
    verbose_name_plural = _("Available choices")

    inlines = [
        EventChoiceOptionInline,
    ]

    fields = ["name", "display_metrics"]
    readonly_fields = ["display_metrics"]

    @admin.display(description=_("Chosen options stats"))
    def display_metrics(self, obj):
        if not obj or not obj.pk:
            return mark_safe(
                f"<span class='text-gray-400'>{_('Save to view selection stats')}</span>"
            )

        options = sorted(
            ((o.get_selected(), o.option, o.max_selected) for o in obj.options.all()),
            reverse=True,
        )
        if not options:
            return mark_safe(
                f"<span class='text-gray-400'>{_('No options configured')}</span>"
            )

        html_lines = []
        for s, n, max_s in options:
            max_text = f"/{max_s}" if max_s is not None else ""
            html_lines.append(
                f"<div class='py-0.5'><span class='font-semibold'>{s}{max_text}</span> : {n}</div>"
            )

        return mark_safe("".join(html_lines))


class EventLinkInline(TabularInline):
    model = EventLink
    tab = True
    extra = 1
    verbose_name_plural = _("Links")

    autocomplete_fields = ["event"]

    form = EventLinkInlineForm


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
    list_filter = (
        "event_type",
        "year",
    )
    list_display = (
        "event_type",
        "name",
        "year",
        "start_datetime",
        "end_datetime",
        "get_event_album_link",
    )
    form = EventAdminForm
    inlines = [
        EventLinkInline,
        EventChoiceInline,
        EventResponseReadonlyInline,
    ]
    list_display_links = ("name",)
    autocomplete_fields = ["event_album"]
    filter_horizontal = ("bartender_whitelist", "bartender_blacklist")
    search_fields = (
        "name",
        "year",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "event_type",
                    "name",
                    "year",
                    "start_datetime",
                    "end_datetime",
                    "response_deadline",
                    "event_album",
                )
            },
        ),
        (
            _("Event details"),
            {"fields": ("location", "description", "internal_description")},
        ),
        (
            _("Bartender access"),
            {
                "fields": (
                    "bartender_whitelist",
                    "bartender_blacklist",
                    "default_may_attends",
                )
            },
        ),
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
