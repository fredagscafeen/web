import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login, logout
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from bartenders.models import BartenderShift, ShiftStreak
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
        return redirect("profile")
    elif EmailTokenBackend.is_bartab_user(email):
        return redirect("bartab")
    else:
        return redirect("/")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


class Login(FormView):
    template_name = "login.html"
    form_class = LoginForm
    success_url = settings.LOGIN_URL

    def form_valid(self, form):
        form.send_email(self.request.GET.get("next"), self.request.path)
        messages.success(
            self.request,
            _(
                "Login mail sendt: Tryk på linket i din modtagede mail for at logge ind."
            ),
        )
        return super().form_valid(form)


class About(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["BEST_MAIL"] = settings.BEST_MAIL
        bartender_shifts = BartenderShift.objects.defer(
            "responsible", "other_bartenders", "period"
        )
        shifts = bartender_shifts.filter(start_datetime__lte=timezone.now())
        shift_streaks = []
        current_streak = None
        found = False
        for shift in shifts:
            if current_streak == None:
                current_streak = ShiftStreak(
                    1, shift.start_datetime, shift.start_datetime
                )
            elif int(shift.start_datetime.strftime("%V")) == int(
                current_streak.end_datetime.strftime("%V")
            ):
                continue
            elif int(shift.start_datetime.strftime("%V")) == int(
                current_streak.end_datetime.strftime("%V")
            ) + 1 or (
                int(current_streak.end_datetime.strftime("%V")) == 52
                and int(shift.start_datetime.strftime("%V")) == 1
            ):
                current_streak = ShiftStreak(
                    current_streak.streak + 1,
                    current_streak.start_datetime,
                    shift.start_datetime,
                )
            else:
                shift_streaks.append(current_streak)
                current_streak = ShiftStreak(
                    1, shift.start_datetime, shift.start_datetime
                )
            if (
                shift.start_datetime >= timezone.now() - datetime.timedelta(days=7)
                and not found
            ):
                current_streak.is_current_shift = True
                found = True
        if current_streak:
            shift_streaks.append(current_streak)
        shift_streak = None
        longest_streak = None
        if found:
            for shift in shift_streaks:
                if shift.is_current_shift:
                    shift_streak = shift
                    break
        elif len(shift_streaks) != 0:
            longest_streak = max(shift_streaks, key=lambda x: x.streak, default=None)
        context["shift_streak"] = shift_streak
        context["longest_streak"] = longest_streak

        return context
