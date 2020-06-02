from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from admin_views.admin import AdminViews
from bartenders.models import BartenderShift
from logentry_admin.admin import LogEntryAdmin

from .forms import SwapForm1, SwapForm2

admin.site.unregister(LogEntry)


@admin.register(LogEntry)
class LogEntryAdminWithSecrets(LogEntryAdmin, AdminViews):
    admin_views = (
        ("Secrets", "secrets_view"),
        ("Swap shifts", "swap_view"),
    )

    def secrets_view(self, request):
        secrets = [
            (key, title, username, getattr(settings, key, None), url)
            for key, title, username, url in settings.SECRET_ADMIN_KEYS
        ]

        context = dict(
            # Include common variables for rendering the admin template.
            self.admin_site.each_context(request),
            # Anything else you want in the context...
            secrets=secrets,
        )
        return TemplateResponse(request, "secrets_admin.html", context)

    def swap_view(self, request):
        try:
            step = int(request.GET.get("step", "0"))
        except ValueError:
            step = 0

        form = None
        valid = False
        if request.method == "POST":
            form = SwapForm1(request.POST)
            if form.is_valid():
                valid = True
                b1 = form.cleaned_data["bartender1"]
                b2 = form.cleaned_data["bartender2"]
                swap = form.cleaned_data["swap"]

            if step == 1 and valid:
                form = SwapForm2(swap=swap, bartender1=b1, bartender2=b2)
            elif step == 2:
                form = SwapForm2(request.POST, swap=swap, bartender1=b1, bartender2=b2)
                if form.is_valid():
                    # Actual swap shifts here
                    shift1 = form.cleaned_data["bartender_shift1"]

                    shift1.replace(b1, b2)

                    if swap:
                        shift2 = form.cleaned_data["bartender_shift2"]
                        shift2.replace(b2, b1)

                    messages.success(request, "Swapped shifts.")
                    return redirect("/admin/")

        if not form:
            form = SwapForm1()
            step = 0
            next_step = 1
        else:
            next_step = step
            if valid:
                next_step += 1

        context = dict(
            # Include common variables for rendering the admin template.
            self.admin_site.each_context(request),
            # Anything else you want in the context...
            form=form,
            form_step=step,
            next_step=next_step,
        )
        return TemplateResponse(request, "swap_admin.html", context)
