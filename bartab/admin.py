import json
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from django.forms.widgets import TextInput
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from bartenders.models import BoardMemberPeriod
from fredagscafeen.admin_view import custom_admin_view
from printer.views import pdf_preview

from .forms import ConsumptionForm
from .models import BarTabEntry, BarTabSnapshot, BarTabUser, SumField


class BarTabEntryReadonlyInline(admin.TabularInline):
    model = BarTabEntry
    fields = ("added", "used")
    readonly_fields = ("added", "used")
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.action(description=_("Hide users from tab"))
def hide_from_tab(self, request, queryset):
    for user in queryset:
        user.hidden_from_tab = True
        user.save()
    self.message_user(
        request,
        ngettext(
            "%d user hidden from tab.",
            "%d users hidden from tab.",
            queryset.count(),
        )
        % queryset.count(),
        messages.SUCCESS,
    )


@admin.action(description=_("Show users on tab"))
def show_on_tab(self, request, queryset):
    for user in queryset:
        user.hidden_from_tab = False
        user.save()
    self.message_user(
        request,
        ngettext(
            "%d user shown on tab.",
            "%d users shown on tab.",
            queryset.count(),
        )
        % queryset.count(),
        messages.SUCCESS,
    )


@admin.register(BarTabUser)
class BarTabUserAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "current_balance", "hidden_from_tab")
    search_fields = ("name", "email")
    list_filter = ("hidden_from_tab",)
    inlines = [
        BarTabEntryReadonlyInline,
    ]
    actions = [hide_from_tab, show_on_tab]

    def current_balance(self, obj):
        return obj.balance_str

    current_balance.admin_order_field = "current_balance"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = BarTabUser.with_balances(qs)
        return qs


class BarTabEntryInline(admin.TabularInline):
    model = BarTabEntry
    fields = ("added_cash", "raw_added", "user", "raw_used")
    extra = 1
    min_num = 1
    formfield_overrides = {
        SumField: {"widget": TextInput},
    }
    autocomplete_fields = ["user"]

    def get_queryset(self, request):
        """Select related prevents 2*N queries when calling entry.__str__ in each form"""
        return super().get_queryset(request).select_related("user", "snapshot")

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "raw_used":
            field.widget.attrs["size"] = "50"
        return field


class BarTabContext:
    file_name = "bartab"
    file_path = "admin/bartab.tex"

    @staticmethod
    def get_context():
        tab_parts = (([], "Aktive"), ([], "Inaktive"))
        for user in BarTabUser.objects.exclude(hidden_from_tab=True):
            tab_parts[not user.is_active][0].append(user)

        latest_tab_update = BarTabSnapshot.objects.first()
        guide_path = settings.MEDIA_ROOT + f"guides/krydsliste.pdf"
        try:
            with open(guide_path, "rb") as f:
                pass
        except FileNotFoundError:
            guide_path = None

        return {
            "tab_parts": tab_parts,
            "pizza_lines": range(33),
            "latest_tab_update": latest_tab_update,
            "logo_path": settings.STATIC_ROOT + f"images/logo_gray.png",
            "guide_path": guide_path,
        }


@admin.register(BarTabSnapshot)
class BarTabSnapshotAdmin(admin.ModelAdmin):
    change_form_template = "admin/enhancedinline.html"
    list_display = (
        "date",
        "entry_count",
        "total_added",
        "total_cash_added",
        "total_card_added",
        "total_used",
    )
    readonly_fields = (
        "last_updated",
        "total_added",
        "total_used",
        "total_cash_added",
        "total_card_added",
    )
    inlines = [BarTabEntryInline]

    def entry_count(self, obj):
        return obj.entries.count()


@custom_admin_view("bartab", "generate bartab")
def generate_bartab(admin, request):
    return pdf_preview(request, admin.admin_site, BarTabContext)


@custom_admin_view("bartab", "top 10 list")
def top_10_consumption(admin, request):
    result = None

    counter = Counter()

    current_period = BoardMemberPeriod.get_current_period()
    if current_period:
        start = current_period.start_date
        end = datetime.now().date()
        snapshot_end = None

        for snapshot in BarTabSnapshot.objects.all():
            if start <= snapshot.datetime.date() <= end:
                for entry in snapshot.entries.all():
                    counter[entry.user] += entry.used

                if snapshot_end is None:
                    snapshot_end = snapshot.datetime.date()

    result = counter.most_common()

    context = dict(
        # Include common variables for rendering the admin template.
        admin.admin_site.each_context(request),
        # Anything else you want in the context...
        title=_("Top 10 listen"),
        start=start,
        end=snapshot_end,
        result=result[:10],
    )
    return TemplateResponse(request, "admin/consumption.html", context)


@custom_admin_view("bartab", "count consumption")
def count_consumption(admin, request):
    result = None

    if request.method == "POST":
        form = ConsumptionForm(request.POST)
        if form.is_valid():
            counter = Counter()

            start = form.cleaned_data["start_snapshot"]
            end = form.cleaned_data["end_snapshot"]

            for snapshot in BarTabSnapshot.objects.all():
                if start.datetime <= snapshot.datetime <= end.datetime:
                    for entry in snapshot.entries.all():
                        counter[entry.user] += entry.used

            result = counter.most_common()
    else:
        form = ConsumptionForm()

    context = dict(
        # Include common variables for rendering the admin template.
        admin.admin_site.each_context(request),
        # Anything else you want in the context...
        form=form,
        result=result,
    )
    return TemplateResponse(request, "admin/consumption.html", context)


@custom_admin_view("bartab", "bartab balance graph")
def bartab_graph(admin, request):
    balances = defaultdict(int)
    graph_data = []
    bartab_snapshots = BarTabSnapshot.objects.defer("last_updated", "notes")
    for snapshot in reversed(bartab_snapshots):
        for entry in snapshot.entries.all():
            balances[entry.user] += entry.added - entry.used

        total_positive = sum(b for b in balances.values() if b > 0)
        total_negative = -sum(b for b in balances.values() if b < 0)

        if snapshot.bartender_shift != None:
            graph_data.append(
                {
                    "datetime": snapshot.datetime.timestamp() * 1000,
                    "total_positive": float(total_positive),
                    "total_negative": float(total_negative),
                }
            )

    context = dict(
        # Include common variables for rendering the admin template.
        admin.admin_site.each_context(request),
        # Anything else you want in the context...
        graph_data=json.dumps(graph_data),
    )
    return TemplateResponse(request, "admin/graph.html", context)
