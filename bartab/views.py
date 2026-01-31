from collections import Counter
from datetime import datetime

from constance import config
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import DetailView

from bartenders.models import BoardMemberPeriod

from .models import BarTabSnapshot, BarTabUser

DEFAULT_ENTRIES_PER_PAGE = "10"


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

        balance = self.object.balance

        context["balance"] = self.format_amount(balance)

        total_used = 0
        context["entries"] = []
        for entry in self.object.entries.all():
            shift = entry.snapshot.bartender_shift

            context["entries"].append(
                {
                    "shift": "Epoch" if not shift else shift.date,
                    "added": entry.added,
                    "used": self.format_amount(entry.used),
                    "balance": self.format_amount(balance),
                }
            )

            balance -= entry.added
            balance += entry.used

            total_used += entry.used

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
            context["entries"], bartab_entries_pages_per_page
        )

        bartab_entries_page_number = self.request.GET.get("bartab_entries_page", 1)
        if not bartab_entries_page_number:
            bartab_entries_page_number = paginator_bartab_entries.num_pages
        bartab_entries_page_obj = paginator_bartab_entries.get_page(
            bartab_entries_page_number
        )

        context["bartab_entries"] = bartab_entries_page_obj

        context["total_used"] = self.format_amount(total_used)

        counter = Counter()
        current_period = BoardMemberPeriod.get_current_period()
        context["current_period"] = current_period

        if config.SHOW_BARTAB_TOP_TEN:
            if current_period:
                start = current_period.start_date
                end = datetime.now().date()
                snapshot_end = None

                for snapshot in BarTabSnapshot.objects.all():
                    if start <= snapshot.date <= end:
                        for entry in snapshot.entries.all():
                            counter[entry.user] += entry.used

                        if snapshot_end is None:
                            snapshot_end = snapshot.datetime.date()

            result = counter.most_common()
            context["top_ten"] = result[:10]
            user_name = self.get_object().name
            context["user_name"] = user_name
            for i in range(len(result)):
                name, value = result[i]
                if str(name) == user_name:
                    context["is_outside_top_ten"] = i + 1 > 10
                    context["user_position"] = i + 1
                    context["user_value"] = value
                    break

        return context

    def format_amount(self, amount):
        return f"{amount:,}".replace(",", "'").replace(".", ",")
