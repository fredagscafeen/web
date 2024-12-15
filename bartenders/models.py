import datetime
from enum import IntEnum
from urllib.parse import urljoin

from django import forms
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.expressions import Case, Value, When
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from fredagscafeen.email import send_template_email

from .mailman2 import Mailman


def template_render(template_str, context):
    t = Template(template_str)
    c = Context(context)
    return t.render(c)


def date_format(dt, format):
    """
    django.utils.formats.date_format doesn't seem to work with l10n,
    even when using use_l10n=True.
    """
    return template_render("{{ dt | date:format }}", {"dt": dt, "format": format})


# Fields shared between Bartender and BartenderApplication.
# All of these should actually be required in BartenderApplication,
# but we enforce that in BartenderApplicationForm for new applications.
class BartenderCommon(models.Model):
    TSHIRT_SIZE_CHOICES = (
        ("XS", "XS"),
        ("S", "S"),
        ("M", "M"),
        ("L", "L"),
        ("XL", "XL"),
        ("XXL", "XXL"),
        ("XXXL", "XXXL"),
    )

    class Meta:
        abstract = True

    name = models.CharField(max_length=140, verbose_name=_("Fulde navn"))
    username = models.CharField(
        max_length=140, unique=True, verbose_name=_("Brugernavn")
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        verbose_name=_("E-mail"),
        help_text=_("En post.au mail fungerer ikke"),
    )
    studentNumber = models.IntegerField(
        blank=False, null=True, verbose_name=_("Studienummer")
    )
    phoneNumber = models.IntegerField(
        blank=True, null=True, verbose_name=_("Telefonnummer")
    )
    tshirt_size = models.CharField(
        max_length=140,
        choices=TSHIRT_SIZE_CHOICES,
        blank=True,
        null=True,
        verbose_name=_("T-shirt størrelse"),
    )


class Bartender(BartenderCommon):
    isActiveBartender = models.BooleanField(default=True)
    prefer_only_early_shifts = models.BooleanField(
        default=False,
        verbose_name=_("Jeg foretrækker ikke at have nogle sene barvagter"),
    )

    @property
    def isBoardMember(self):
        period = BoardMemberPeriod.get_current_period()
        return self.board_members.filter(period=period).exists()

    class Meta:
        ordering = (
            "-isActiveBartender",
            "name",
        )

    @property
    def symbol(self):
        if self.isBoardMember:
            return "★ "
        elif self.isActiveBartender:
            return ""
        else:
            return "✝ "

    @property
    def first_bartender_shift(self):
        return BartenderShift.with_bartender(self).first()

    @property
    def last_bartender_shift(self):
        return BartenderShift.with_bartender(self).last()

    @property
    def first_deposit_shift(self):
        return BoardMemberDepositShift.with_bartender(self).first()

    MAILMAN_ALL = (
        settings.MAILMAN_ALL_LIST,
        getattr(settings, "MAILMAN", None),
    )
    MAILMAN_BEST = (
        settings.MAILMAN_BEST_LIST,
        getattr(settings, "MAILMAN", None),
    )

    def _get_mailman(self, list_and_password):
        return Mailman(settings.MAILMAN_URL_BASE, *list_and_password)

    def is_on_mailing_list(self, list_and_password=MAILMAN_ALL):
        # TODO: Fix mailman implementation
        return True
        """
        mailman = self._get_mailman(list_and_password)
        return self.email in mailman.get_subscribers()
        """

    def add_to_mailing_list(self, list_and_password=MAILMAN_ALL):
        # TODO: Fix mailman implementation
        return
        mailman = self._get_mailman(list_and_password)
        mailman.add_subscriptions([f"{self.name} <{self.email}>"])

    def remove_from_mailing_list(self, list_and_password=MAILMAN_ALL):
        # TODO: Fix mailman implementation
        return
        mailman = self._get_mailman(list_and_password)
        mailman.remove_subscriptions([self.email])

    @classmethod
    def shift_ordered(cls):
        period = BoardMemberPeriod.get_current_period()
        board_members = cls.objects.filter(board_members__period=period)
        return cls.objects.annotate(
            order=Case(
                When(id__in=board_members, then=Value(0)),
                When(isActiveBartender=True, then=Value(1)),
                default=2,
                output_field=models.IntegerField(),
            )
        ).order_by("order", "name")

    def __str__(self):
        return f"{self.symbol}{self.name} ({self.username})"


class BartenderUnavailableDate(models.Model):
    bartender = models.ForeignKey(
        Bartender, on_delete=models.CASCADE, related_name="unavailable_dates"
    )
    date = models.DateField()

    class Meta:
        unique_together = ("bartender", "date")


class BoardMember(models.Model):
    bartender = models.ForeignKey(
        Bartender, on_delete=models.CASCADE, related_name="board_members"
    )
    period = models.ForeignKey("BoardMemberPeriod", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    responsibilities = models.CharField(max_length=255)
    image = models.ImageField(upload_to="boardMembers", blank=True, null=True)

    class Meta:
        unique_together = ("bartender", "period")
        ordering = (
            "period",
            "title",
        )

    def __str__(self):
        return self.bartender.username


class BoardMemberPeriod(models.Model):
    start_date = models.DateField(unique=True)

    class Meta:
        ordering = ("-start_date",)

    @property
    def end_date(self):
        try:
            next_start = self.get_next_by_start_date().start_date
            return next_start - datetime.timedelta(days=1)
        except BoardMemberPeriod.DoesNotExist:
            return None

    @property
    def approx_end_date(self):
        GENERAL_ASSEMBLY_MONTH = 3

        end_date = self.end_date
        if end_date == None:
            end_date = self.start_date.replace(month=GENERAL_ASSEMBLY_MONTH)
            if end_date <= self.start_date:
                end_date = end_date.replace(year=end_date.year + 1)

        return end_date

    @property
    def end_date_display(self):
        d = self.end_date

        if d == None:
            return "..."

        return d

    @classmethod
    def get_current_period(cls):
        today = timezone.localdate()
        return cls.objects.filter(start_date__lte=today).first()

    def __str__(self):
        start_year = self.start_date.year
        til = _("til")
        return f"{start_year} / {start_year + 1} ({self.start_date} {til} {self.end_date_display})"


class BartenderApplication(BartenderCommon):
    study = models.CharField(max_length=50, verbose_name=_("Studie"))
    study_year = models.IntegerField(verbose_name=_("Årgang"))
    info = models.TextField(
        blank=False,
        help_text=_(
            "Fortæl lidt om dig selv, og hvorfor du tror at lige præcist du, ville være en god bartender"
        ),
    )

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created",)

    def _send_accept_email(self):
        URLS = [
            "barplan",
            "guides",
            "profile",
        ]

        text_format = {"name": self.name}
        html_format = {"name": self.name}

        for url_name in URLS:
            url = urljoin(settings.SELF_URL, reverse(url_name))
            link_name = f"{url_name}_link"
            text_format[link_name] = f"her: {url}"
            html_format[link_name] = mark_safe(f'<a href="{url}">her</a>')

        return send_template_email(
            subject=f"Bartendertilmelding: {self.name}",
            body_template="""Hej {name},

Din ansøgning om at blive bartender ved Fredagscaféen er blevet accepteret.
Scheduleren vil tildele dig barvagter, når den nye barplan bliver lavet.
Du kan se barplanen {barplan_link} og du kan markere, hvilke dage du ikke
kan stå i bar {profile_link}.
Du er blevet tilføjet til vores mailing liste (alle@fredagscafeen.dk).

Husk at læse bartenderguides'ne, som kan ses {guides_link}.

Ses i baren! :)

/Bestyrelsen""",
            text_format=text_format,
            html_format=html_format,
            to=[self.email],
            cc=["best@fredagscafeen.dk"],
        )

    def accept(self):
        self.email = self.email if self.email is None else self.email.lower()
        common_fields = super()._meta.get_fields()
        value_dict = {f.name: getattr(self, f.name) for f in common_fields}
        b = Bartender.objects.create(**value_dict)

        try:
            if settings.MAILMAN_MUTABLE:
                b.add_to_mailing_list()

            self._send_accept_email()
        except:
            # Delete as something went wrong
            b.delete()
            raise

        return b.pk

    def __str__(self):
        return self.username


Weekday = IntEnum(
    "Weekday", "MONDAY TUESDAY WEDNESDAY THURSDAY FRIDAY SATURDAY SUNDAY", start=0
)


def next_date_with_weekday(date, weekday):
    date += datetime.timedelta(1)
    while date.weekday() != weekday:
        date += datetime.timedelta(1)

    return date


def next_bartender_shift_start(last_date=None):
    """
    Returns the next friday after the last shift

    Can't be a class method, because we need to use this as a default value
    """
    if last_date == None:
        last_shift = BartenderShift.objects.last()
        if last_shift:
            last_date = last_shift.end_datetime.date()
        else:
            last_date = timezone.now().date() - datetime.timedelta(1)

    next_date = next_date_with_weekday(last_date, Weekday.FRIDAY)
    dt = datetime.datetime.combine(next_date, BartenderShift.DEFAULT_START_TIME)
    tz = timezone.get_current_timezone()
    aware_datetime = timezone.make_aware(dt, tz)
    return aware_datetime


def next_bartender_shift_dates(count):
    d = next_bartender_shift_start().date()
    for i in range(count):
        yield d
        d = next_bartender_shift_start(d).date()


def next_deposit_shift_start(last_date=None):
    """
    Returns the next monday after the last shift

    Can't be a class method, because we need to use this as a default value
    """
    if last_date == None:
        last_shift = BoardMemberDepositShift.objects.last()
        if last_shift:
            last_date = last_shift.end_date
        else:
            last_date = timezone.now().date() - datetime.timedelta(1)

    return next_date_with_weekday(last_date, Weekday.MONDAY)


class BartenderShiftPeriod(models.Model):
    class Meta:
        ordering = ("-generation_datetime",)

    generation_datetime = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Generated at {self.generation_datetime}"

    @classmethod
    def current(cls):
        return cls.objects.first()


class BartenderShift(models.Model):
    # This can't be a timezone aware time because of DST
    DEFAULT_START_TIME = datetime.time(15, 00)
    DEFAULT_SHIFT_DURATION = datetime.timedelta(hours=7)

    start_datetime = models.DateTimeField(default=next_bartender_shift_start)
    end_datetime = models.DateTimeField(blank=True)
    responsible = models.ForeignKey(Bartender, on_delete=models.PROTECT)
    other_bartenders = models.ManyToManyField(
        Bartender, related_name="shifts", blank=True
    )

    period = models.ForeignKey(
        BartenderShiftPeriod,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="shifts",
    )

    class Meta:
        ordering = ("start_datetime",)

    def save(self, *args, **kwargs):
        if not self.end_datetime:
            self.end_datetime = self.start_datetime + self.DEFAULT_SHIFT_DURATION

        super().save(*args, **kwargs)

    def all_bartenders(self):
        return [self.responsible] + list(self.other_bartenders.all())

    @classmethod
    def with_bartender(self, bartender):
        # You can't use filter as it returns multiple of the same object:
        # return self.objects.filter(Q(responsible=bartender) | Q(other_bartenders=bartender))

        return self.objects.exclude(
            ~Q(responsible=bartender), ~Q(other_bartenders=bartender)
        )

    def has_multiple_shifts(self):
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(
            datetime.datetime.combine(self.date, datetime.time()), tz
        )
        end = start + datetime.timedelta(days=1)
        return (
            BartenderShift.objects.filter(
                start_datetime__gte=start, start_datetime__lte=end
            ).count()
            > 1
        )

    def display_str(self):
        s = date_format(self.date, "d M")
        if self.has_multiple_shifts():
            s += f' ({date_format(self.start_datetime, "H")} - {date_format(self.end_datetime, "H")})'

        return s

    def is_with_bartender(self, bartender):
        return bartender in self.all_bartenders()

    def compare_to_current_week(self):
        date = timezone.now().date()
        less_than_week = self.start_datetime.date() <= date + datetime.timedelta(4)
        greater_than_week = self.end_datetime.date() >= date - datetime.timedelta(2)
        if less_than_week and greater_than_week:
            return 0
        elif less_than_week:
            return -1
        else:
            return 1

    def replace(self, b1, b2):
        if self.responsible == b1:
            self.responsible = b2
            self.save()
        else:
            self.other_bartenders.remove(b1)
            self.other_bartenders.add(b2)
            self.save()

    @property
    def date(self):
        return self.start_datetime.date()

    def __str__(self):
        return f'{self.date}: Responsible: {self.responsible.name}, Other bartenders: {", ".join(b.name for b in self.other_bartenders.all())}'


class BoardMemberDepositShiftPeriod(models.Model):
    generation_datetime = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Generated at {self.generation_datetime}"


class BoardMemberDepositShift(models.Model):
    start_date = models.DateField(default=next_deposit_shift_start)
    end_date = models.DateField(blank=True)
    responsibles = models.ManyToManyField(Bartender, related_name="deposit_shifts")

    period = models.ForeignKey(
        BoardMemberDepositShiftPeriod, on_delete=models.PROTECT, blank=True, null=True
    )

    class Meta:
        ordering = ("start_date",)

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = next_date_with_weekday(self.start_date, Weekday.SUNDAY)

        super().save(*args, **kwargs)

    @classmethod
    def with_bartender(cls, bartender):
        return cls.objects.filter(responsibles=bartender)

    def is_with_bartender(self, bartender):
        return bartender in self.responsibles.all()

    def compare_to_current_week(self):
        date = timezone.now().date()
        less_than_week = self.start_date < date
        greater_than_week = self.end_date > date - datetime.timedelta(1)
        if less_than_week and greater_than_week:
            return 0
        elif less_than_week:
            return -1
        else:
            return 1

    def __str__(self):
        return (
            f'{self.start_date}: {", ".join(b.name for b in self.responsibles.all())}'
        )


class Poll(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class BallotLink(models.Model):
    poll = models.ForeignKey(Poll, models.CASCADE)
    bartender = models.ForeignKey(Bartender, models.CASCADE)
    url = models.URLField()
