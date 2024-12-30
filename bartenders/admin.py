import datetime
from collections import Counter

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions

from bartenders.models import (
    BallotLink,
    Bartender,
    BartenderApplication,
    BartenderShift,
    BartenderShiftPeriod,
    BoardMember,
    BoardMemberDepositShift,
    BoardMemberPeriod,
    Poll,
)
from fredagscafeen.admin_filters import NonNullFieldListFilter
from fredagscafeen.admin_view import custom_admin_view
from printer.views import pdf_preview

from .mailman2 import MailmanError

User = get_user_model()


class FreeBeerListContext:
    file_name = "free_beer_list"
    file_path = "free_beer_list.tex"

    @staticmethod
    def get_context():
        MONTHS = 3

        names = [b.name for b in Bartender.objects.filter(isActiveBartender=True)]
        months = []
        dt = datetime.datetime(1, timezone.now().month, 1)
        for _ in range(MONTHS):
            months.append(dt.strftime("%B"))
            next_month = dt.month + 1
            if next_month == 13:
                next_month = 1
            dt = dt.replace(month=next_month)

        return {
            "names": names,
            "months": months,
        }


@admin.register(Bartender)
class BartenderAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ("name", "username", "email")
    search_fields = ("name", "username", "email")
    list_filter = ("isActiveBartender", ("board_members", NonNullFieldListFilter))

    change_actions = (
        "add_to_mailing_list",
        "remove_from_mailing_list",
        "create_admin_user",
    )

    def add_to_mailing_list(self, request, obj):
        if not settings.MAILMAN_MUTABLE:
            messages.error(request, "MAILMAN_MUTABLE is false!")
            return

        try:
            obj.add_to_mailing_list()
            messages.info(request, "Successfully added to mailing list")
        except MailmanError as e:
            messages.error(request, f"Got Mailman error: {e}")

    add_to_mailing_list.label = "Add to mailing list"

    def remove_from_mailing_list(self, request, obj):
        if not settings.MAILMAN_MUTABLE:
            messages.error(request, "MAILMAN_MUTABLE is false!")
            return

        try:
            obj.remove_from_mailing_list()
            messages.info(request, "Successfully removed from mailing list")
        except MailmanError as e:
            messages.error(request, f"Got Mailman error: {e}")

    remove_from_mailing_list.label = "Remove from mailing list"

    def create_admin_user(self, request, obj):
        first_name, last_name = obj.name.rsplit(" ", maxsplit=1)
        user = User.objects.create(
            username=obj.username,
            email=obj.email,
            first_name=first_name,
            last_name=last_name,
        )

        password = User.objects.make_random_password(length=30)
        user.set_password(password)

        user.is_staff = True
        user.save()

        messages.info(request, f"Created user {obj.username} with password {password}")

    create_admin_user.label = "Create admin user"


@custom_admin_view("bartenders", "generate free beer list")
def generate_free_beer_list(admin, request):
    return pdf_preview(request, admin.admin_site, FreeBeerListContext)


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "bartender", "title", "period")
    list_display_links = ("thumbnail", "bartender")
    list_select_related = ("bartender",)
    list_filter = ("period",)

    def thumbnail(self, obj):
        return (
            mark_safe('<img src="%s" width="75px"/>' % obj.image.url)
            if obj.image
            else "<missing>"
        )


@admin.register(BartenderApplication)
class BartenderApplicationAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ("name", "created", "username", "email")

    change_actions = ("accept", "deny")

    def accept(self, request, obj):
        pk = obj.accept()
        obj.delete()
        return HttpResponseRedirect(
            reverse("admin:bartenders_bartender_change", args=(pk,))
        )

    def deny(self, request, obj):
        obj.delete()
        return HttpResponseRedirect(
            reverse("admin:bartenders_bartenderapplication_changelist")
        )


@admin.register(BartenderShift)
class BartenderShiftAdmin(admin.ModelAdmin):
    list_display = ("start_datetime", "shift_responsible", "other_bartenders_list")
    filter_horizontal = ("other_bartenders",)

    def shift_responsible(self, obj):
        return obj.responsible.name

    def other_bartenders_list(self, obj):
        return ", ".join([s.name for s in obj.other_bartenders.all()])

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "responsible":
            kwargs["queryset"] = Bartender.shift_ordered()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(BoardMemberDepositShift)
class BoardMemberDepositShiftAdmin(admin.ModelAdmin):
    list_display = ("start_date", "end_date", "responsible_board_members")
    filter_horizontal = ("responsibles",)

    def responsible_board_members(self, obj):
        return ", ".join([s.name for s in obj.responsibles.all()])

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "responsibles":
            kwargs["queryset"] = Bartender.shift_ordered()

        return super().formfield_for_manytomany(db_field, request, **kwargs)


class BoardMemberInline(admin.StackedInline):
    model = BoardMember


@admin.register(BoardMemberPeriod)
class BoardMemberPeriodAdmin(admin.ModelAdmin):
    inlines = [BoardMemberInline]


@admin.register(BartenderShiftPeriod)
class BartenderShiftPeriodAdmin(admin.ModelAdmin):
    change_form_template = "bartender_shift_period_change_form.html"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}

        obj = BartenderShiftPeriod.objects.get(id=object_id)

        bartender_shifts = Counter()
        for shift in obj.shifts.all():
            for b in shift.all_bartenders():
                bartender_shifts[b] += 1

        extra_context["bartender_shifts"] = sorted(
            bartender_shifts.items(), key=lambda x: (-x[1], x[0].name)
        )

        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    pass


@custom_admin_view("bartenders", "Bartender shift streaks")
def streaks_view(admin, request):
    bartender_shifts = BartenderShift.objects.defer(
        "responsible", "other_bartenders", "period"
    )
    shifts = bartender_shifts.filter(end_datetime__lte=timezone.now())
    shift_streaks = []
    for shift in shifts:
        shift_streaks.append(shift.streak())
    sorted_shift_streaks = sorted(shift_streaks, key=lambda x: x[0], reverse=True)
    sorted_shift_streaks_short = []
    for shift in sorted_shift_streaks:
        found = False
        for sorted_shift in sorted_shift_streaks_short:
            if shift[1] == sorted_shift[1]:
                found = True
                break
        if not found:
            sorted_shift_streaks_short.append(shift)

    current_shift = shifts.filter(
        start_datetime__lte=timezone.now() + datetime.timedelta(days=2),
        end_datetime__gte=timezone.now() - datetime.timedelta(days=5),
    )
    shift_placement = 0
    if current_shift:
        for i, (streak, start_date, end_date) in enumerate(sorted_shift_streaks_short):
            if end_date == current_shift[0].end_datetime:
                shift_placement = i + 1
                break

    context = dict(
        # Include common variables for rendering the admin template.
        admin.admin_site.each_context(request),
        # Anything else you want in the context...
        shift_streaks=sorted_shift_streaks_short,
        shift_placement=shift_placement,
    )
    return TemplateResponse(request, "streak_admin.html", context)
