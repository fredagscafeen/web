from constance import config
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django_ical.views import ICalFeed

from bartenders.models import Bartender

from .forms import EventResponseForm
from .models import Event

DEFAULT_EVENTS_PER_PAGE = 15


class Events(TemplateView):
    template_name = "events.html"

    def _get_bartender(self):
        if not self.request.user.is_authenticated:
            return None

        try:
            return Bartender.objects.get(email=self.request.user.email)
        except Bartender.DoesNotExist:
            return None

    def _get_base_queryset(self):
        return Event.objects.select_related("event_album").prefetch_related(
            "links", "responses", "bartender_whitelist", "bartender_blacklist"
        )

    def _filter_by_event_type(self, queryset):
        if config.SHOW_COMMON_EVENTS:
            return queryset
        else:
            return queryset.filter(event_type=Event.EventType.INTERNAL)

    def _parse_events_per_page(self):
        events_per_page = self.request.GET.get("events_per_page")
        if (
            not events_per_page
            or events_per_page == "0"
            or events_per_page == ""
            or not events_per_page.isdigit()
            or int(events_per_page) <= 0
        ):
            return DEFAULT_EVENTS_PER_PAGE
        return int(events_per_page)

    def _build_events_data(self, page_obj, bartender):
        may_attend_default = Event.may_attend_default(bartender) if bartender else None
        now = timezone.now()
        seen_years = set()
        events_data = []

        for event in page_obj:
            data = {"event": event}
            if event.year not in seen_years:
                data["year"] = event.year
                seen_years.add(event.year)
            if event.start_datetime > now:
                data["future"] = True

            not_answered = False
            if bartender and event.response_deadline and event.response_deadline >= now:
                if event.may_attend(bartender, may_attend_default):
                    answered = any(
                        r.bartender_id == bartender.id for r in event.responses.all()
                    )
                    not_answered = not answered
            data["not_answered"] = not_answered

            events_data.append(data)

        return events_data

    def _get_upcoming_events_data(self, bartender):
        queryset = self._get_base_queryset()
        queryset = self._filter_by_event_type(queryset)
        now = timezone.now()
        queryset = queryset.filter(start_datetime__gte=now).order_by("start_datetime")

        return {
            "upcoming_events_data": self._build_events_data(queryset, bartender),
        }

    def _get_past_events_data(self, bartender, events_per_page):
        queryset = self._get_base_queryset()
        queryset = self._filter_by_event_type(queryset)
        now = timezone.now()
        queryset = queryset.filter(start_datetime__lt=now).order_by("-start_datetime")

        page_num = self.request.GET.get("event_page", 1)
        paginator = Paginator(queryset, events_per_page)
        page_obj = paginator.get_page(page_num)

        return {
            "past_page_obj": page_obj,
            "past_events_data": self._build_events_data(page_obj, bartender),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bartender = self._get_bartender()
        events_per_page = self._parse_events_per_page()

        context["is_bartender"] = bartender is not None
        context["events_per_page"] = events_per_page

        context.update(self._get_upcoming_events_data(bartender))
        context.update(self._get_past_events_data(bartender, events_per_page))

        return context


class EventFeed(ICalFeed):
    product_id = "-//fredagscafeen.dk//Events//EN"
    timezone = "UTC"
    file_name = "events.ics"
    title = _("Bartender Events")

    def items(self):
        return Event.objects.filter(event_type=Event.EventType.INTERNAL).all()

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


class CommonEventFeed(ICalFeed):
    product_id = "-//fredagscafeen.dk//CommonEvents//EN"
    timezone = "UTC"
    file_name = "common_events.ics"
    title = _("Common Events")

    def items(self):
        return Event.objects.filter(event_type=Event.EventType.COMMON).all()

    def item_title(self, event):
        return event.name

    def item_start_datetime(self, event):
        return event.start_datetime

    def item_end_datetime(self, event):
        return event.end_datetime

    def item_description(self, event):
        return event.description

    def item_link(self, event):
        return f"{settings.SELF_URL}common-events/"

    def item_guid(self, event):
        return f"common-event-{event.pk}@fredagscafeen.dk"


class EventView(Events):
    template_name = "event.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()

        context["load_no_answers"] = self.request.GET.get("load_no_answers")

        event_id = self.request.resolver_match.kwargs["event_id"]
        event = get_object_or_404(Event, id=event_id)

        bartender = self._get_bartender()

        may_attend = False
        if bartender:
            may_attend = event.may_attend(bartender)

        if may_attend:
            context["form"] = EventResponseForm(event=event, bartender=bartender)

        if event.start_datetime > now:
            context["future"] = True

        context["bartender"] = bartender
        context["event"] = event
        context["may_attend"] = may_attend

        return context

    def post(self, request, *args, **kwargs):
        try:
            event_id = request.POST.get("event_id")
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return HttpResponseBadRequest(_("Event with id does not exist"))

        bartender = self._get_bartender()
        if not bartender or not event.may_attend(bartender):
            return HttpResponseForbidden(_("Not logged in as an active bartender"))

        if not event.response_deadline:
            return HttpResponseForbidden(_("This event does not take responses"))

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
