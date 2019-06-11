import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import REDIRECT_FIELD_NAME

from email_auth.auth import EmailTokenBackend
from bartab.models import BarTabUser, BarTabSnapshot
from guides.models import Guide
from items.models import Item
from udlejning.models import Udlejning, UdlejningApplication, UdlejningGrill
from web.forms import UdlejningApplicationForm, LoginForm


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


class Login(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = settings.LOGIN_URL

    def form_valid(self, form):
        form.send_email(self.request.GET.get('next'))
        messages.success(self.request, 'Login mail sendt: Tryk på linket i din modtagede mail for at logge ind.')
        return super().form_valid(form)


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
