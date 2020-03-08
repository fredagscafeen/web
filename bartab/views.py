from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from .models import BarTabSnapshot, BarTabUser


class BarTab(LoginRequiredMixin, DetailView):
    model = BarTabUser
    template_name = "bartab.html"

    def get_object(self):
        try:
            return BarTabUser.objects.get(email=self.request.user.email)
        except BarTabUser.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["update_date"] = BarTabSnapshot.objects.first().date
        context["credit_hold_limit"] = BarTabUser.CREDIT_HOLD_LIMIT

        if not self.object:
            return context

        total_used = 0

        balance = self.object.balance

        context["entries"] = []
        for entry in self.object.entries.all():
            shift = entry.snapshot.bartender_shift

            context["entries"].append(
                {
                    "shift": "Epoch" if not shift else shift.date,
                    "added": entry.added,
                    "used": entry.used,
                    "balance": balance,
                }
            )

            balance -= entry.added
            balance += entry.used

            total_used += entry.used

        context["total_used"] = total_used

        return context
