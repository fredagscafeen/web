import urllib.request
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.views.generic import TemplateView, ListView, CreateView
from django_ical.views import ICalFeed

from bartenders.models import Bartender, BoardMember, BartenderApplication, BartenderShift, BoardMemberDepositShift
from items.models import Item
from udlejning.models import Udlejning
from udlejning.models import UdlejningGrill
from web.forms import BartenderApplicationForm


class Index(CreateView):
    model = BartenderApplication
    template_name = 'index.html'
    form_class = BartenderApplicationForm
    success_url = '/'

    def form_valid(self, form):
        # Call super to save instance
        response = super().form_valid(form)

        # Send email to best
        form.send_email(self.object.pk)
        messages.success(self.request, 'Your application has been sent successfully.')

        return response


class Contact(TemplateView):
    template_name = "contact.html"


class BartenderList(TemplateView):
    template_name = "bartenders.html"

    def get_context_data(self, **kwargs):
        context = super(BartenderList, self).get_context_data(**kwargs)
        context['bartenders'] = Bartender.objects.filter(isActiveBartender=True)
        context['inactive_bartenders'] = Bartender.objects.filter(isActiveBartender=False)
        return context


class Barplan(TemplateView):
    template_name = "barplan.html"

    def get_context_data(self, **kwargs):
        context = super(Barplan, self).get_context_data(**kwargs)
        context['bartendershifts'] = BartenderShift.objects.filter(Q(date__gte=datetime.today()))
        context['boardmemberdepositshifts'] = BoardMemberDepositShift.objects.all()
        return context

class ShiftEvent:
    def __init__(self):
        self.guid = 0


class UserBarplan(ICalFeed):
    product_id = '-//example.com//Example//EN'
    timezone = 'UTC'
    file_name = "barvagter.ics"
    title = "Barvagter"

    def get_object(self, request, *args, **kwargs):
        return kwargs

    def items(self, kwargs):
        response = urllib.request.urlopen(
            "https://calendar.google.com/calendar/ical/1dt8kqlgn9mgen53otb33ag9pg%40group.calendar.google.com/public/basic.ics")
        data = response.read()
        text = data.decode('utf-8')
        lineiterator = iter(text.splitlines())
        eventlist = []
        currentevent = ShiftEvent()
        for line in lineiterator:
            if "BEGIN:VEVENT" in line:
                currentevent = ShiftEvent()
            if "UID:" in line:
                currentevent.uid = line[4:]
            if "SUMMARY:" in line:
                currentevent.summary = line[8:]
            if "DESCRIPTION:" in line:
                currentevent.description = line[12:]
            if "DTSTART;" in line:
                if "Europe/Copenhagen" in line:
                    currentevent.dtstart = datetime.strptime(line[len("DTSTART;TZID=Europe/Copenhagen:"):],
                                                             "%Y%m%dT%H%M%S")
                    currentevent.startstamp = line[len("DTSTART;TZID=Europe/Copenhagen:"):]
            if "DTEND;" in line:
                if "Europe/Copenhagen" in line:
                    currentevent.dtend = datetime.strptime(line[len("DTEND;TZID=Europe/Copenhagen:"):], "%Y%m%dT%H%M%S")
            if "LOCATION:" in line:
                currentevent.location = line[9:]
            if "END:VEVENT" in line:
                if kwargs['username'] in currentevent.summary:
                    currentevent.uid += currentevent.startstamp
                    eventlist.append(currentevent)
        return eventlist

    def item_guid(self, item):
        return item.uid

    def item_title(self, item):
        return item.summary

    def item_location(self, item):
        return item.location

    def item_start_datetime(self, item):
        return item.dtstart

    def item_end_datetime(self, item):
        return item.dtend

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        return f"{settings.SELF_URL}barplan/"


class Items(ListView):
    template_name = "items.html"
    allow_empty = True
    model = Item
    context_object_name = 'items'
    ordering = ('name',)


class Search(ListView):
    template_name = "search.html"
    allow_empty = True
    model = Item
    context_object_name = 'items'


class Board(ListView):
    template_name = "board.html"
    allow_empty = True
    model = BoardMember
    context_object_name = 'boardmembers'


class Udlejninger(ListView):
    template_name = "udlejning.html"
    allow_empty = True
    queryset = Udlejning.objects.filter(paid=False, dateFrom__gte=timezone.now()-timedelta(days=30))
    context_object_name = 'udlejninger'


class UdlejningerGrill(ListView):
    template_name = "udlejningGrill.html"
    allow_empty = True
    queryset = UdlejningGrill.objects.filter(dateFrom__gte=timezone.now()-timedelta(days=30))
    context_object_name = 'udlejningerGrill'


class Guides(TemplateView):
    template_name = "guides.html"
