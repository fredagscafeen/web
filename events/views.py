from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django_ical.views import ICalFeed

from bartenders.models import Bartender

from .forms import EventResponseForm
from .models import Event

DEFAULT_EVENTS_PER_PAGE = 3


class Events(TemplateView):
    template_name = "events.html"

    def get_bartender(self):
        if not self.request.user.is_authenticated:
            return None

        try:
            return Bartender.objects.get(email=self.request.user.email)
        except Bartender.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        events_per_page = self.request.GET.get("events_per_page")
        if (
            not events_per_page
            or events_per_page == "0"
            or events_per_page == ""
            or not events_per_page.isdigit()
            or int(events_per_page) <= 0
        ):
            events_per_page = DEFAULT_EVENTS_PER_PAGE
        context["events_per_page"] = events_per_page

        events = Event.objects.defer(
            "description", "bartender_whitelist", "bartender_blacklist"
        )

        paginator_events = Paginator(events, events_per_page)

        event_page = self.request.GET.get("event_page", 1)
        event_page_obj = paginator_events.get_page(event_page)
        context["event_page_obj"] = event_page_obj

        bartender = self.get_bartender()

        seen_years = set()
        events_data = []

        for event in event_page_obj:
            data = {"event": event}
            if event.year not in seen_years:
                data["year"] = event.year
                seen_years.add(event.year)
            events_data.append(data)

        context["bartender"] = bartender
        context["events_data"] = events_data

        return context


class EventFeed(ICalFeed):
    product_id = "-//fredagscafeen.dk//Events//EN"
    timezone = "UTC"
    file_name = "events.ics"
    title = _("Bartender Events")

    def items(self):
        return Event.objects.all()

    def item_title(self, event):
        return event.name

    def item_location(self, event):
        return event.location

    def item_start_datetime(self, event):
        return event.start_datetime

    def item_end_datetime(self, event):
        return event.end_datetime

    def item_description(self, event):
        tilmeldingsfrist = _("Tilmeldingsfrist")
        return f"""{tilmeldingsfrist}: {event.response_deadline}

{event.description}"""

    def item_link(self, event):
        return f"{settings.SELF_URL}events/"

    def item_guid(self, event):
        return f"event-{event.pk}@fredagscafeen.dk"


class EventView(TemplateView):
    template_name = "event.html"

    def get_bartender(self):
        if not self.request.user.is_authenticated:
            return None

        try:
            return Bartender.objects.get(email=self.request.user.email)
        except Bartender.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event_id = self.request.resolver_match.kwargs["event_id"]
        event = get_object_or_404(Event, id=event_id)

        bartender = self.get_bartender()

        if bartender and event.may_attend(bartender):
            context["form"] = EventResponseForm(event=event, bartender=bartender)

        context["bartender"] = bartender
        context["event"] = event
        if bartender:
            context["may_attend"] = Event.may_attend_default(bartender)

        context["DOMAIN"] = settings.DOMAIN

        return context

    def post(self, request, *args, **kwargs):
        try:
            event_id = request.POST.get("event_id")
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return HttpResponseBadRequest(_("Event with id does not exist"))

        bartender = self.get_bartender()
        if not bartender or not event.may_attend(bartender):
            return HttpResponseForbidden(_("Not logged in as an active bartender"))

        form = EventResponseForm(request.POST, event=event, bartender=bartender)
        if not form.is_valid():
            for error in form.errors.values():
                messages.error(request, f"{error}")
            return redirect("event", event_id)

        form.save()

        messages.success(
            request,
            _("Opdateret tilmelding til %(event_name)s") % {"event_name": event.name},
        )
        return redirect("event", event_id)
