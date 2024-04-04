import datetime

from django.contrib import messages
from django.utils import timezone
from django.views.generic import CreateView, ListView

from .forms import UdlejningApplicationForm
from .models import (
    Udlejning,
    UdlejningApplication,
    UdlejningGrill,
    UdlejningProjector,
    UdlejningSpeakers,
)


class Udlejninger(CreateView):
    model = UdlejningApplication
    template_name = "udlejning.html"
    form_class = UdlejningApplicationForm
    success_url = "/udlejning/#"  # Don't scroll to form on success

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["udlejninger"] = Udlejning.objects.filter(
            dateFrom__gte=timezone.now() - datetime.timedelta(days=30)
        )
        return context

    def form_valid(self, form):
        # Call super to save instance
        response = super().form_valid(form)

        # Send email to best
        form.send_email(self.object.pk)
        messages.success(
            self.request,
            "Din anmodning om at låne fadølsanlægget er modtaget. Vi vender tilbage til dig med et svar hurtigst muligt.",
        )

        return response


class UdlejningerGrill(ListView):
    template_name = "udlejningGrill.html"
    allow_empty = True
    queryset = UdlejningGrill.objects.filter(
        dateFrom__gte=timezone.now() - datetime.timedelta(days=30)
    )
    context_object_name = "udlejningerGrill"


class UdlejningerProjector(ListView):
    template_name = "udlejningProjector.html"
    allow_empty = True
    queryset = UdlejningProjector.objects.filter(
        dateFrom__gte=timezone.now() - datetime.timedelta(days=30)
    )


class UdlejningerSpeakers(ListView):
    template_name = "udlejningSpeakers.html"
    allow_empty = True
    queryset = UdlejningSpeakers.objects.filter(
        dateFrom__gte=timezone.now() - datetime.timedelta(days=30)
    )
