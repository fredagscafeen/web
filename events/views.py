from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django_ical.views import ICalFeed

from bartenders.models import Bartender

from .forms import EventResponseForm
from .models import Event


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

        show_all = "show_all" in self.request.GET
        context["show_all"] = show_all
        qs = Event.objects.all()
        if not show_all:
            qs = qs[:3]

        bartender = self.get_bartender()

        events_data = []
        for event in qs:
            data = {"event": event}
            if bartender and event.may_attend(bartender):
                data["form"] = EventResponseForm(event=event, bartender=bartender)
            events_data.append(data)

        context["bartender"] = bartender
        context["events_data"] = events_data
        if bartender:
            context["may_attend"] = Event.may_attend_default(bartender)

        return context

    def post(self, request, *args, **kwargs):
        try:
            event_id = request.POST.get("event_id")
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return HttpResponseBadRequest("Event with id does not exist")

        bartender = self.get_bartender()
        if not bartender or not event.may_attend(bartender):
            return HttpResponseForbidden("Not logged in as an active bartender")

        form = EventResponseForm(request.POST, event=event, bartender=bartender)
        if not form.is_valid():
            for error in form.errors.values():
                messages.error(request, f"{error}")
            return redirect("events")

        form.save()

        messages.success(request, f"Opdateret tilmelding til {event.name}")
        return redirect("events")


class EventFeed(ICalFeed):
    product_id = "-//fredagscafeen.dk//Events//EN"
    timezone = "UTC"
    file_name = "events.ics"
    title = "Bartender Events"

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
        return f"""Tilmeldingsfrist: {event.response_deadline}

{event.description}"""

    def item_link(self, event):
        return f"{settings.SELF_URL}events/"

    def item_guid(self, event):
        return f"event-{event.pk}@fredagscafeen.dk"
