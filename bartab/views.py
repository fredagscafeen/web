from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import DetailView

from .models import BarTabSnapshot, BarTabUser

DEFAULT_ENTRIES_PER_PAGE = 10


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

        context["latest_tab_update"] = BarTabSnapshot.objects.first()
        context["credit_hold_limit"] = BarTabUser.CREDIT_HOLD_LIMIT

        if not self.object:
            return context

        bartab_entries_pages_per_page = self.request.GET.get(
            "bartab_entries_pages_per_page"
        )
        if (
            not bartab_entries_pages_per_page
            or bartab_entries_pages_per_page == "0"
            or bartab_entries_pages_per_page == ""
            or not bartab_entries_pages_per_page.isdigit()
        ):
            bartab_entries_pages_per_page = DEFAULT_ENTRIES_PER_PAGE
        context["bartab_entries_pages_per_page"] = bartab_entries_pages_per_page

        paginator_bartab_entries = Paginator(
            self.object.entries.all(), bartab_entries_pages_per_page
        )

        bartab_entries_page_number = self.request.GET.get("bartab_entries_page", 1)
        if not bartab_entries_page_number:
            bartab_entries_page_number = paginator_bartab_entries.num_pages
        bartab_entries_page_obj = paginator_bartab_entries.get_page(
            bartab_entries_page_number
        )

        context["bartab_entries"] = bartab_entries_page_obj

        balance = self.object.balance
        total_used = 0
        context["entries"] = []
        for entry in bartab_entries_page_obj:
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
