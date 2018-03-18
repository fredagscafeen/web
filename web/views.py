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


class UserBarplan(ICalFeed):
    product_id = '-//fredagscafeen.dk//UserBarplan//EN'
    timezone = 'UTC'
    file_name = "barvagter.ics"
    title = "Barvagter"

    def get_object(self, request, **kwargs):
        # kwargs['username'] is None if we need to show all shifts
        return kwargs.get('username')

    def items(self, username):
        if username:
            return BartenderShift.with_bartender(username)
        else:
            return BartenderShift.objects.all()

    def item_title(self, shift):
        return " + ".join(b.username for b in shift.all_bartenders())

    def item_start_datetime(self, shift):
        return shift.date

    def item_end_datetime(self, shift):
        return shift.date

    def item_description(self, shift):
        return f'''Responsible: {shift.responsible.name}
Other bartenders: {", ".join(b.name for b in shift.other_bartenders.all())}'''

    def item_link(self, shift):
        return f"{settings.SELF_URL}barplan/"


class UserDepositShifts(ICalFeed):
    product_id = '-//fredagscafeen.dk//UserDepositShifts//EN'
    timezone = 'UTC'
    file_name = "pantvagter.ics"
    title = "Pantvagter"

    def get_object(self, request, **kwargs):
        # kwargs['username'] is None if we need to show all shifts
        return kwargs.get('username')

    def items(self, username):
        if username:
            return BoardMemberDepositShift.with_bartender(username)
        else:
            return BoardMemberDepositShift.objects.all()

    def item_title(self, shift):
        return " + ".join(b.username for b in shift.responsibles.all())

    def item_start_datetime(self, shift):
        return shift.date

    def item_end_datetime(self, shift):
        return shift.date

    def item_description(self, shift):
        return f'''Responsibles: {", ".join(b.name for b in shift.responsibles.all())}'''

    def item_link(self, shift):
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
