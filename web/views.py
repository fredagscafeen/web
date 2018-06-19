import datetime
from itertools import groupby
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView, ListView, CreateView
from django.views.generic.edit import UpdateView, FormView
from django_ical.views import ICalFeed
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST

from bartenders.models import Bartender, BoardMember, BartenderApplication, BartenderShift, BoardMemberDepositShift, next_bartender_shift_dates, BartenderUnavailableDate
from items.models import Item
from udlejning.models import Udlejning
from udlejning.models import UdlejningGrill
from web.forms import BartenderApplicationForm, BartenderInfoForm, LoginForm


@require_GET
def email_login_view(request, username, token):
    user = authenticate(username=username, token=token)
    if user:
        login(request, user)
    return redirect('profile')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


class BartenderInfo(PermissionRequiredMixin, UpdateView):
    login_url = '/login/'
    redirect_field_name = None

    model = Bartender
    template_name = 'bartender_info.html'
    form_class = BartenderInfoForm

    UNAVAILABLE_DATES = 52

    def has_permission(self):
        try:
            return self.request.user.has_perm('bartenders.change_bartender', self.get_object())
        except Bartender.DoesNotExist:
            return False

    def get_object(self, queryset=None):
        return Bartender.objects.get(username=self.request.user.username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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

        self.object.unavailable_dates.all().delete()
        for ordinal in self.request.POST.getlist('unavailable_ordinals'):
            date = datetime.date.fromordinal(int(ordinal))
            BartenderUnavailableDate(date=date, bartender=self.object).save()

        return redirect_url

    def get_success_url(self):
        return self.request.path


class Login(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = '/login/'

    def form_valid(self, form):
        form.send_email()
        messages.success(self.request, 'Login mail sendt: Tryk på linket i din modtagede mail for at logge ind.')
        return super().form_valid(form)


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
        context = super().get_context_data(**kwargs)
        context['bartenders'] = Bartender.objects.filter(isActiveBartender=True)
        context['inactive_bartenders'] = Bartender.objects.filter(isActiveBartender=False)
        return context


class Barplan(TemplateView):
    template_name = "barplan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bartendershifts'] = BartenderShift.objects.filter(end_datetime__gte=timezone.now() - datetime.timedelta(1))
        context['boardmemberdepositshifts'] = BoardMemberDepositShift.objects.filter(end_date__gte=timezone.now() - datetime.timedelta(1))
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
    queryset = Udlejning.objects.filter(paid=False, dateFrom__gte=timezone.now()-datetime.timedelta(days=30))
    context_object_name = 'udlejninger'


class UdlejningerGrill(ListView):
    template_name = "udlejningGrill.html"
    allow_empty = True
    queryset = UdlejningGrill.objects.filter(dateFrom__gte=timezone.now()-datetime.timedelta(days=30))
    context_object_name = 'udlejningerGrill'


class Guides(TemplateView):
    template_name = "guides.html"
