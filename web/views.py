from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import REDIRECT_FIELD_NAME

from email_auth.auth import EmailTokenBackend
from web.forms import LoginForm


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


class Login(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = settings.LOGIN_URL

    def form_valid(self, form):
        form.send_email(self.request.GET.get('next'))
        messages.success(self.request, 'Login mail sendt: Tryk på linket i din modtagede mail for at logge ind.')
        return super().form_valid(form)


class Contact(TemplateView):
    template_name = "contact.html"
