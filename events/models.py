import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender, BartenderShiftPeriod, BoardMemberPeriod
from events.utils import get_year
from gallery.models import Album
from web.models import TimeStampedModel


class Event(TimeStampedModel):
    class EventType(models.TextChoices):
        COMMON = "common", _("Common Event")
        INTERNAL = "internal", _("Bartender event")

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.INTERNAL,
        verbose_name=_("Event type"),
        help_text=_(
            "Common events are visible to all bartenders, while bartender events are only visible to bartenders who are allowed to attend."
        ),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("The visible name of the event."),
    )
    year = models.PositiveSmallIntegerField(
        default=get_year,
        verbose_name=_("Årgang"),
        help_text=_("The year of the event."),
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    event_album = models.ForeignKey(
        Album,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="events",
        verbose_name=_("Event album"),
        help_text=_("The album associated with the event."),
    )

    location = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_("Location"),
        help_text=_("The location of the event."),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Public description"),
        help_text=_("A description of the event. This will be visible to all users."),
    )

    internal_description = models.TextField(
        blank=True,
        verbose_name=_("Internal description"),
        help_text=_(
            "This will display for bartenders instead of the public description. Leave blank to use the public description. This is useful for internal information that should not be visible to the public. For example when the event is common but it has internal information for bartenders."
        ),
    )

    # --- BARTENDER EVENTS ONLY ---
    response_deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Response deadline"),
        help_text=_("The deadline for bartenders to respond to the event invitation."),
    )
    bartender_whitelist = models.ManyToManyField(
        Bartender,
        related_name="whitelisted_events",
        blank=True,
        help_text=_(
            "Bartenders who are allowed to attend the event. If empty, all bartenders are allowed to attend."
        ),
    )
    bartender_blacklist = models.ManyToManyField(
        Bartender,
        related_name="blacklisted_events",
        blank=True,
        help_text=_(
            "Bartenders who are not allowed to attend the event. If empty, all bartenders are allowed to attend."
        ),
    )

    class Meta:
        ordering = ("-start_datetime",)

    def __str__(self):
        return f"{self.year}: {self.name}"

    def is_main_link(self):
        """This is only temporary until the CommonEvent model is removed. It is to maintain compatibility with the existing templates."""
        if self.event_album_id:
            return True
        return self.links.exists()

    def get_main_link(self):
        """This is only temporary until the CommonEvent model is removed. It is to maintain compatibility with the existing templates."""
        if self.event_album:
            return self.event_album.get_absolute_url()

        first_link = self.links.first()
        if first_link:
            return first_link.url
        return None

    def get_main_link_icon(self):
        """This is only temporary until the CommonEvent model is removed. It is to maintain compatibility with the existing templates."""
        if self.event_album:
            return "image"

        first_link = self.links.first()
        if first_link:
            return first_link.get_icon()
        return "link-45deg"

    def is_bartender_event(self):
        return self.event_type == self.EventType.INTERNAL

    def deadline_exceeded(self):
        if not self.response_deadline:
            return False
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

    def may_attend(self, bartender, default_result=None):
        if bartender in self.bartender_blacklist.all():
            return False
        if bartender in self.bartender_whitelist.all():
            return True

        if default_result is not None:
            return default_result

        return self.may_attend_default(bartender)


class EventChoice(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("The visible name of the choice."),
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_choices",
        verbose_name=_("Event"),
        help_text=_("The event this choice is associated with."),
    )

    def __str__(self):
        return f"{self.event}: {self.name}"


class EventChoiceOption(models.Model):
    class Meta:
        unique_together = ("event_choice", "option")

    event_choice = models.ForeignKey(
        EventChoice,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name=_("Event choice"),
        help_text=_("The event choice this option is associated with."),
    )
    option = models.CharField(
        max_length=255,
        verbose_name=_("Option"),
        help_text=_("The visible name of the option."),
    )
    max_selected = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_(
            "The maximum number of bartenders that can select this option. Leave blank for no limit."
        ),
    )

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


class EventLink(models.Model):
    class EventLinkType(models.TextChoices):
        """Mapping from TYPE -> (type, display-label)"""

        FACEBOOK = "facebook", _("Facebook")
        INSTAGRAM = "instagram", _("Instagram")
        LINKEDIN = "linkedin", _("LinkedIn")
        TWITTER = "twitter", _("Twitter")
        YOUTUBE = "youtube", _("YouTube")
        OTHER = "other", _("Other")

        @property
        def icon(self):
            icons = {
                self.FACEBOOK: "facebook",
                self.INSTAGRAM: "instagram",
                self.LINKEDIN: "linkedin",
                self.TWITTER: "twitter",
                self.YOUTUBE: "youtube",
                self.OTHER: "link-45deg",
            }
            return icons.get(self, "link-45deg")

    type = models.CharField(
        max_length=20,
        choices=EventLinkType.choices,
        default=EventLinkType.FACEBOOK,
        verbose_name=_("Link type"),
        help_text=_(
            "The type of link. This determines the default title and icon for the link."
        ),
    )
    title = models.CharField(
        max_length=25,
        verbose_name=_("Title"),
        blank=True,
        help_text=_(
            "Override the displayed title of the link. Leave blank to use the default title for the link type."
        ),
    )
    url = models.URLField(verbose_name=_("URL"), help_text=_("The URL of the link."))

    event = models.ForeignKey(  # Adds the "links" field to the Event model with a Many to One relationship
        Event,
        on_delete=models.CASCADE,
        related_name="links",
        verbose_name=_("Event"),
        help_text=_("The event this link is associated with."),
    )

    def get_title(self):
        if self.title:
            return self.title
        return self.EventLinkType(self.type).label

    def get_icon(self):
        return self.EventLinkType(self.type).icon


class EventResponse(models.Model):
    class Meta:
        unique_together = ("event", "bartender")

    event = models.ForeignKey(  # Adds the "responses" field to the Event model with a Many to One relationship
        Event,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name=_("Event"),
        help_text=_("The event this response is associated with."),
    )
    bartender = models.ForeignKey(  # Adds the "event_responses" field to the Bartender model with a Many to One relationship
        Bartender,
        on_delete=models.CASCADE,
        related_name="event_responses",
        verbose_name=_("Bartender"),
        help_text=_("The bartender who submitted this response."),
    )
    attending = models.BooleanField(
        help_text=_("Whether the bartender is attending the event.")
    )
    selected_options = models.ManyToManyField(  # Adds the "event_responses" field to the EventChoiceOption model with a Many to Many relationship
        EventChoiceOption,
        related_name="event_responses",
        verbose_name=_("Selected options"),
        help_text=_("The options selected by the bartender for this event response."),
    )

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
        ordering = ("date",)

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
            else "link-45deg"
        )
