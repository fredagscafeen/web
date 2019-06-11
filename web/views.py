import datetime
from itertools import groupby
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils import timezone
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.views.generic.edit import UpdateView, FormView
from django_ical.views import ICalFeed
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import REDIRECT_FIELD_NAME

from email_auth.auth import EmailTokenBackend
from bartab.models import BarTabUser, BarTabSnapshot
from bartenders.models import Bartender, BoardMember, BartenderApplication, BartenderShift, BoardMemberDepositShift, next_bartender_shift_dates, BartenderUnavailableDate, BoardMemberPeriod
from guides.models import Guide
from items.models import Item
from udlejning.models import Udlejning, UdlejningApplication, UdlejningGrill
from events.models import Event, EventResponse
from web.forms import BartenderApplicationForm, UdlejningApplicationForm, BartenderInfoForm, LoginForm, EventResponseForm


@require_GET
def email_login_view(request, email, token):
    user = authenticate(email=email, token=token)
    if user:
        login(request, user)

    next = request.GET.get(REDIRECT_FIELD_NAME)
    if next:
        return redirect(next)

    if EmailTokenBackend.is_bartender(email):
        return redirect('profile')
    elif EmailTokenBackend.is_bartab_user(email):
        return redirect('bartab')
    else:
        return redirect('/')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


class BartenderInfo(LoginRequiredMixin, UpdateView):
    model = Bartender
    template_name = 'bartender_info.html'
    form_class = BartenderInfoForm

    UNAVAILABLE_DATES = 52

    def get_object(self):
        try:
            return Bartender.objects.get(email=self.request.user.email)
        except Bartender.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            future_dates = list(next_bartender_shift_dates(self.UNAVAILABLE_DATES))

            unavailable_dates = set(d.date for d in self.object.unavailable_dates.filter(date__gte=future_dates[0], date__lte=future_dates[-1]))

            dates_table = []
            for _, dates in groupby(future_dates, key=lambda d: d.month):
                dates = list(dates)
                dates_table.append((dates[0], [(d.toordinal(), d, d in unavailable_dates) for d in dates]))

            context['dates_table'] = dates_table

        return context

    def form_valid(self, form):
        messages.success(self.request, 'Profil opdateret')
        redirect_url = super().form_valid(form)

        if 'deactivate' in self.request.POST:
            self.object.isActiveBartender = False
            self.object.save()
        elif 'subscribe_maillist' in self.request.POST:
            self.object.add_to_mailing_list()
        elif 'unsubscribe_maillist' in self.request.POST:
            self.object.remove_from_mailing_list()


        self.object.unavailable_dates.all().delete()
        for ordinal in self.request.POST.getlist('unavailable_ordinals'):
            date = datetime.date.fromordinal(int(ordinal))
            BartenderUnavailableDate(date=date, bartender=self.object).save()

        return redirect_url

    def get_success_url(self):
        return self.request.path


class BarTab(LoginRequiredMixin, DetailView):
    model = BarTabUser
    template_name = 'bartab.html'

    def get_object(self):
        try:
            return BarTabUser.objects.get(email=self.request.user.email)
        except BarTabUser.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['update_date'] = BarTabSnapshot.objects.first().date
        context['credit_hold_limit'] = BarTabUser.CREDIT_HOLD_LIMIT

        if not self.object:
            return context

        total_used = 0

        balance = self.object.balance

        context['entries'] = []
        for entry in self.object.entries.all():
            shift = entry.snapshot.bartender_shift

            context['entries'].append({
                'shift': 'Epoch' if not shift else shift.date,
                'added': entry.added,
                'used': entry.used,
                'balance': balance,
            })

            balance -= entry.added
            balance += entry.used

            total_used += entry.used

        context['total_used'] = total_used

        return context


class Events(TemplateView):
    template_name = 'events.html'

    def get_bartender(self):
        if not self.request.user.is_authenticated:
            return None

        try:
            return Bartender.objects.get(email=self.request.user.email)
        except Bartender.DoesNotExist:
            return None


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bartender = self.get_bartender()

        events_data = []
        for event in Event.objects.all():
            data = {'event': event}
            if bartender and bartender.isActiveBartender:
                data['form'] = EventResponseForm(event=event, bartender=bartender)
                data['enabled'] = timezone.now() <= event.response_deadline
            events_data.append(data)

        context['bartender'] = bartender
        context['events_data'] = events_data

        return context


    def post(self, request, *args, **kwargs):
        bartender = self.get_bartender()
        if not bartender or not bartender.isActiveBartender:
            return HttpResponseForbidden('Not logged in as an active bartender')

        try:
            event_id = request.POST.get('event_id')
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return HttpResponseBadRequest('Event with id does not exist')

        form = EventResponseForm(request.POST, event=event, bartender=bartender)
        if not form.is_valid():
            return HttpResponseBadRequest('Invalid form')

        form.save()

        messages.success(request, f'Opdateret tilmelding til {event.name}')
        return redirect('events')


class Login(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = settings.LOGIN_URL

    def form_valid(self, form):
        form.send_email(self.request.GET.get('next'))
        messages.success(self.request, 'Login mail sendt: Tryk på linket i din modtagede mail for at logge ind.')
        return super().form_valid(form)


class Index(CreateView):
    model = BartenderApplication
    template_name = 'index.html'
    form_class = BartenderApplicationForm
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            barshift_guide = Guide.objects.get(name='Guide til en standard barvagt')
            context['barshift_guide_url'] = barshift_guide.document.url
        except Guide.DoesNotExist:
            context['barshift_guide_url'] = '<missing>'

        return context

    def form_valid(self, form):
        # Call super to save instance
        response = super().form_valid(form)

        # Send email to best
        form.send_email(self.object.pk)
        messages.success(self.request, 'Din ansøgning er blevet indsendt.')

        return response


class Udlejninger(CreateView):
    model = UdlejningApplication
    template_name = 'udlejning.html'
    form_class = UdlejningApplicationForm
    success_url = '/udlejning/#'  # Don't scroll to form on success

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['udlejninger'] = Udlejning.objects.filter(dateFrom__gte=timezone.now()-datetime.timedelta(days=30))
        return context

    def form_valid(self, form):
        # Call super to save instance
        response = super().form_valid(form)

        # Send email to best
        form.send_email(self.object.pk)
        messages.success(self.request, 'Din anmodning om at låne fadølsanlægget er modtaget. Vi vender tilbage til dig med et svar hurtigst muligt.')

        return response


class Contact(TemplateView):
    template_name = "contact.html"


class BartenderList(TemplateView):
    template_name = "bartenders.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bartenders'] = Bartender.objects.filter(isActiveBartender=True)
        context['inactive_bartenders'] = Bartender.objects.filter(isActiveBartender=False)
        return context


class Barplan(TemplateView):
    template_name = "barplan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        show_all = 'show_all' in self.request.GET

        context['show_all'] = show_all

        if show_all:
            end_datetime = timezone.make_aware(datetime.datetime.utcfromtimestamp(0))
        else:
            end_datetime = timezone.now() - datetime.timedelta(1)

        context['bartendershifts'] = BartenderShift.objects.filter(end_datetime__gte=end_datetime)
        context['boardmemberdepositshifts'] = BoardMemberDepositShift.objects.filter(end_date__gte=end_datetime)

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
            bartender = get_object_or_404(Bartender, username=username)
            return BartenderShift.with_bartender(bartender)
        else:
            return BartenderShift.objects.all()

    def item_title(self, shift):
        return " + ".join(b.username for b in shift.all_bartenders())

    def item_start_datetime(self, shift):
        return shift.start_datetime

    def item_end_datetime(self, shift):
        return shift.end_datetime

    def item_description(self, shift):
        return f'''Responsible: {shift.responsible.name}
Other bartenders: {", ".join(b.name for b in shift.other_bartenders.all())}'''

    def item_link(self, shift):
        return f"{settings.SELF_URL}barplan/"

    def item_guid(self, shift):
        return f'barshift-{shift.pk}@fredagscafeen.dk'


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
            bartender = get_object_or_404(Bartender, username=username)
            return BoardMemberDepositShift.with_bartender(bartender)
        else:
            return BoardMemberDepositShift.objects.all()

    def item_title(self, shift):
        return " + ".join(b.username for b in shift.responsibles.all())

    def item_start_datetime(self, shift):
        return shift.start_date

    def item_end_datetime(self, shift):
        return shift.end_date

    def item_description(self, shift):
        return f'''Responsibles: {", ".join(b.name for b in shift.responsibles.all())}'''

    def item_link(self, shift):
        return f"{settings.SELF_URL}barplan/"

    def item_guid(self, shift):
        return f'depositshift-{shift.pk}@fredagscafeen.dk'


class EventFeed(ICalFeed):
    product_id = '-//fredagscafeen.dk//Events//EN'
    timezone = 'UTC'
    file_name = 'events.ics'
    title = 'Events'

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
        return f'''Tilmeldingsfrist: {event.response_deadline}

{event.description}'''

    def item_link(self, event):
        return f'{settings.SELF_URL}events/'

    def item_guid(self, event):
        return f'event-{event.pk}@fredagscafeen.dk'


class Items(ListView):
    template_name = "items.html"
    allow_empty = True
    model = Item
    context_object_name = 'items'
    ordering = ('name',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        items_data = []
        for item in Item.objects.all():
            items_data.append({
                'brewery': item.brewery.name if item.brewery else None,
                'name': item.name,
                'price': item.priceInDKK,
                'barcode': item.barcode,
                'id': item.id,
            })

        context['items_data'] = items_data

        return context


class Search(ListView):
    template_name = "search.html"
    allow_empty = True
    model = Item
    context_object_name = 'items'


class Board(ListView):
    template_name = "board.html"
    allow_empty = True
    model = BoardMemberPeriod
    context_object_name = 'periods'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['periods'] = context['periods'].filter(start_date__lte=timezone.localdate())

        periods = context['periods']

        data = []

        intervals = {}

        for period in periods.all():
            for boardmember in period.boardmember_set.all():
                intervals.setdefault(boardmember.bartender, []).append((period.start_date, period.approx_end_date))

        merged_intervals = []
        for bartender, ints in intervals.items():
            prev_start = None
            for i, (start, end) in enumerate(ints):
                if prev_start == end + datetime.timedelta(days=1):
                    merged_intervals[-1][1] = start
                else:
                    merged_intervals.append([bartender, start, end])

                prev_start = start

        merged_intervals.sort(key=lambda x: (-x[2].toordinal(), -x[1].toordinal()))

        for bartender, start, end in merged_intervals:
            data.append([f'{start.month}/{start.year}', f'{end.month}/{end.year}', bartender.name, 'default'])

        timesheet_data = {
            'start': periods.last().start_date.year,
            'end': periods.first().start_date.year + 1,
            'data': data,
        }

        context['timesheet_data'] = timesheet_data

        return context


class UdlejningerGrill(ListView):
    template_name = "udlejningGrill.html"
    allow_empty = True
    queryset = UdlejningGrill.objects.filter(dateFrom__gte=timezone.now()-datetime.timedelta(days=30))
    context_object_name = 'udlejningerGrill'


class Guides(TemplateView):
    template_name = "guides.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        guides = []
        for k, name in Guide.GUIDE_TYPES:
            guides.append((name, Guide.objects.filter(category=k)))

        context['guides'] = guides

        return context
