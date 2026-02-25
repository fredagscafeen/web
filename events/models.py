import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender, BartenderShiftPeriod, BoardMemberPeriod
from events.utils import get_year
from gallery.models import Album
from web.models import TimeStampedModel


class EventChoice(models.Model):
    name = models.CharField(max_length=255)
    event = models.ForeignKey(
        "Event", on_delete=models.CASCADE, related_name="event_choices"
    )

    def __str__(self):
        return f"{self.event}: {self.name}"


class EventChoiceOption(models.Model):
    class Meta:
        unique_together = ("event_choice", "option")

    event_choice = models.ForeignKey(
        EventChoice, on_delete=models.CASCADE, related_name="options"
    )
    option = models.CharField(max_length=255)
    max_selected = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        selected = self.get_selected()
        if self.max_selected:
            return f"{self.option} ({selected}, max {self.max_selected})"
        return f"{self.option} ({selected})"

    def get_selected(self):
        return EventResponse.objects.filter(selected_options=self).count()

    def can_more_choose(self):
        return self.max_selected == None or self.get_selected() < self.max_selected

    def can_bartender_choose(self, bartender):
        if self.can_more_choose():
            return True

        try:
            response = EventResponse.objects.get(
                event=self.event_choice.event, bartender=bartender
            )
            return response.get_option(self.event_choice) == self
        except EventResponse.DoesNotExist:
            return False


class Event(TimeStampedModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )
    location = models.CharField(
        max_length=255,
        verbose_name=_("Location"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )
    year = models.PositiveSmallIntegerField(default=get_year, verbose_name=_("Årgang"))
    event_album = models.ForeignKey(
        Album,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="album",
        verbose_name=_("Event album"),
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    response_deadline = models.DateTimeField(
        verbose_name=_("Response deadline"),
    )
    bartender_whitelist = models.ManyToManyField(
        Bartender,
        related_name="whitelisted_events",
        blank=True,
    )
    bartender_blacklist = models.ManyToManyField(
        Bartender,
        related_name="blacklisted_events",
        blank=True,
    )

    class Meta:
        unique_together = ("name", "year")
        ordering = ("-start_datetime",)

    def __str__(self):
        return f"{self.year}: {self.name}"

    def deadline_exceeded(self):
        return timezone.now() > self.response_deadline

    def attending_count(self):
        return sum(r.attending for r in self.responses.all())

    def not_attending_count(self):
        return sum(not r.attending for r in self.responses.all())

    def no_answer_count(self):
        return (
            sum(self.may_attend(b) for b in Bartender.objects.all())
            - self.not_attending_count()
            - self.attending_count()
        )

    def sorted_responses(self):
        return sorted(self.responses.all(), key=lambda r: r.bartender.name)

    def sorted_no_answer(self):
        no_answer = [
            b
            for b in Bartender.objects.all()
            if self.may_attend(b) and not self.responses.filter(bartender=b).exists()
        ]
        return sorted(no_answer, key=lambda r: r.name)

    def sorted_choices(self):
        return self.event_choices.order_by("id")

    @classmethod
    def may_attend_default(cls, bartender):
        # Allow active bartenders
        if bartender.isActiveBartender:
            return True

        # Allow board members that have been active for atleast one day between now and 1 year ago
        period_count = BoardMemberPeriod.objects.filter(
            start_date__gt=datetime.datetime.today() - datetime.timedelta(days=365)
        ).count()
        allowed_periods = BoardMemberPeriod.objects.all()[: period_count + 1]
        for period in allowed_periods:
            if period.boardmember_set.filter(bartender=bartender).exists():
                return True

        # Allow bartenders who had a shift the current period of shifts,
        # but are no longer active.
        # Also allow bartenders who had a shift in the previous shift period,
        # if it ended before 31 days ago
        MAX_INACTIVE_TIME = timezone.timedelta(days=31)
        last_shift = bartender.last_bartender_shift
        if last_shift:
            last_period = last_shift.period
            current_period = BartenderShiftPeriod.current()
            if last_period == current_period:
                return True

            previous_period = BartenderShiftPeriod.objects.all()[1]
            if last_period == previous_period:
                time_since_period_end = (
                    timezone.now() - current_period.generation_datetime
                )
                if time_since_period_end <= MAX_INACTIVE_TIME:
                    return True

        return False

    def may_attend(self, bartender):
        if self.bartender_blacklist.filter(id=bartender.id).exists():
            return False

        if self.bartender_whitelist.filter(id=bartender.id).exists():
            return True

        return self.may_attend_default(bartender)


class EventResponse(models.Model):
    class Meta:
        unique_together = ("event", "bartender")

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="responses")
    bartender = models.ForeignKey(Bartender, on_delete=models.CASCADE)
    attending = models.BooleanField()
    selected_options = models.ManyToManyField(EventChoiceOption)

    def __str__(self):
        return f"{self.event}, {self.bartender}: {self.attending}"

    def _assert_event_has_event_choice(self, event_choice):
        assert self.event.event_choices.filter(id=event_choice.id).exists()

    def clear_option(self, event_choice):
        self._assert_event_has_event_choice(event_choice)
        self.selected_options.remove(
            *self.selected_options.filter(event_choice=event_choice)
        )

    def set_option(self, option):
        assert self.can_set_option(option)
        self.clear_option(option.event_choice)
        self.selected_options.add(option)

    def can_set_option(self, option):
        return option.can_bartender_choose(self.bartender)

    def get_option(self, event_choice):
        self._assert_event_has_event_choice(event_choice)

        try:
            return self.selected_options.get(event_choice=event_choice)
        except EventChoiceOption.DoesNotExist:
            return None

    def get_sorted_options(self):
        return sorted(self.selected_options.all(), key=lambda o: o.event_choice.id)


class CommonEvent(models.Model):
    class Meta:
        ordering = ("-date",)

    title = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )
    url = models.URLField(blank=True, verbose_name=_("Link to additional information"))

    def __str__(self):
        return "%s: %s" % (self.date, self.title)

    def url_bs_icon(self):
        url_is_internal = settings.DOMAIN in f"{self.url}"
        if url_is_internal:
            return "image"
        return (
            "facebook"
            if "facebook.com" in f"{self.url}" or "fb.com" in f"{self.url}"
            else "box-arrow-up-right"
        )
