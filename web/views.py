import urllib.request

from django.utils.datetime_safe import datetime
from django.views.generic import TemplateView
from django.http import HttpResponse

from bartenders.models import Bartender, BoardMember
from django_ical.views import ICalFeed
from items.models import Item


class Index(TemplateView):
    template_name = "index.html"


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


class ShiftEvent:
    def __init__(self):
        self.guid = 0


class UserBarplan(ICalFeed):
    product_id = '-//example.com//Example//EN'
    timezone = 'Europe/Copenhagen'
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
            if "DTEND;" in line:
                if "Europe/Copenhagen" in line:
                    currentevent.dtend = datetime.strptime(line[len("DTEND;TZID=Europe/Copenhagen:"):], "%Y%m%dT%H%M%S")
            if "LOCATION:" in line:
                currentevent.location = line[9:]
            if "END:VEVENT" in line:
                if kwargs['username'] in currentevent.summary:
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
        return "http://fredagscafeen.dk/barplan/"


class Items(TemplateView):
    template_name = "items.html"

    def get_context_data(self, **kwargs):
        context = super(Items, self).get_context_data(**kwargs)
        context['items'] = Item.objects.all()
        return context


class Search(TemplateView):
    template_name = "search.html"

    def get_context_data(self, **kwargs):
        context = super(Search, self).get_context_data(**kwargs)
        context['items'] = Item.objects.all()
        return context


class Board(TemplateView):
    template_name = "board.html"

    def get_context_data(self, **kwargs):
        context = super(Board, self).get_context_data(**kwargs)
        context['boardmembers'] = BoardMember.objects.filter()
        return context
