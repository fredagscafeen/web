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
    ReleasedBartenderShift,
    ShiftStreak,
)
from fredagscafeen.admin_filters import NonNullFieldListFilter
from fredagscafeen.admin_view import custom_admin_view
from printer.views import pdf_preview

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

    change_actions = ("create_admin_user",)

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
    list_display = ("thumbnail", "bartender", "responsibilities", "title", "period")
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


@admin.register(ReleasedBartenderShift)
class ReleasedBartenderShiftAdmin(admin.ModelAdmin):
    list_display = ("bartender", "bartender_shift")


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
    shifts = bartender_shifts.filter(start_datetime__lte=timezone.now())
    shift_streaks = []
    current_streak = None
    found = False
    for shift in shifts:
        if current_streak == None:
            current_streak = ShiftStreak(1, shift.start_datetime, shift.start_datetime)
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
            current_streak = ShiftStreak(1, shift.start_datetime, shift.start_datetime)
        if (
            shift.start_datetime >= timezone.now() - datetime.timedelta(days=7)
            and not found
        ):
            current_streak.is_current_shift = True
            found = True
    shift_streaks.append(current_streak)

    sorted_shift_streaks = sorted(shift_streaks, reverse=True)

    context = dict(
        # Include common variables for rendering the admin template.
        admin.admin_site.each_context(request),
        # Anything else you want in the context...
        shift_streaks=sorted_shift_streaks,
    )
    return TemplateResponse(request, "streak_admin.html", context)
