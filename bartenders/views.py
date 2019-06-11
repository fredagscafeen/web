import datetime
from itertools import groupby
from django.views.generic import TemplateView, CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_ical.views import ICalFeed
from guides.models import Guide
from .models import Bartender, BartenderApplication, BartenderShift, BoardMemberDepositShift, BoardMemberPeriod, next_bartender_shift_dates, BartenderUnavailableDate
from .forms import BartenderApplicationForm, BartenderInfoForm


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
