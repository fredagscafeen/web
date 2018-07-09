from urllib.parse import urljoin

import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils.crypto import get_random_string
from enum import IntEnum

from .mailman2 import Mailman
from fredagscafeen.email import send_template_email


EMAIL_TOKEN_LENGTH = 64
def new_email_token():
    return get_random_string(EMAIL_TOKEN_LENGTH)


# Fields shared between Bartender and BartenderApplication.
# All of these should actually be required in BartenderApplication,
# but we enforce that in BartenderApplicationForm for new applications.
class BartenderCommon(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=140, verbose_name='Fulde navn')
    username = models.CharField(max_length=140, unique=True, verbose_name='Brugernavn')
    email = models.CharField(max_length=255, blank=True)
    studentNumber = models.IntegerField(blank=True, null=True, verbose_name='Studienummer')
    phoneNumber = models.IntegerField(blank=True, null=True, verbose_name='Telefonnummer')


class Bartender(BartenderCommon):
    TSHIRT_SIZE_CHOICES = (
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('XXXL', 'XXXL'),
    )

    isActiveBartender = models.BooleanField(default=True)
    tshirt_size = models.CharField(choices=TSHIRT_SIZE_CHOICES, max_length=10, blank=True, null=True, verbose_name='T-shirt størrelse')
    email_token = models.CharField(max_length=EMAIL_TOKEN_LENGTH, default=new_email_token, editable=False)

    @property
    def isBoardMember(self):
        try:
            self.boardmember
            return True
        except BoardMember.DoesNotExist:
            return False

    class Meta:
        ordering = ('-isActiveBartender', 'name',)

    @property
    def symbol(self):
        if self.isBoardMember:
            return '★ '
        elif self.isActiveBartender:
            return ''
        else:
            return '✝ '

    @property
    def first_bartender_shift(self):
        return BartenderShift.with_bartender(self).first()

    @property
    def first_deposit_shift(self):
        return BoardMemberDepositShift.with_bartender(self).first()

    def _get_mailman(self):
        return Mailman(settings.MAILMAN_URL_BASE,
                       settings.MAILMAN_ALL_LIST,
                       settings.MAILMAN_ALL_PASSWORD)

    def add_to_mailing_list(self):
        mailman = self._get_mailman()
        mailman.add_subscriptions([f'{self.name} <{self.email}>'])

    def remove_from_mailing_list(self):
        mailman = self._get_mailman()
        mailman.remove_subscriptions([self.email])

    def __str__(self):
        return f'{self.symbol}{self.name} ({self.username})'


class BartenderUnavailableDate(models.Model):
    bartender = models.ForeignKey(Bartender, on_delete=models.CASCADE, related_name='unavailable_dates')
    date = models.DateField()

    class Meta:
        unique_together = ('bartender', 'date')


class BoardMember(models.Model):
    bartender = models.OneToOneField(Bartender, on_delete=models.CASCADE, primary_key=True)
    title = models.CharField(max_length=255)
    responsibilities = models.CharField(max_length=255)
    image = models.ImageField(upload_to='boardMembers', blank=True, null=True)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.bartender.username


class BartenderApplication(BartenderCommon):
    info = models.TextField(blank=True, help_text='Eventuelle ekstra info til bestyrelsen skrives her')

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created', )

    def _send_accept_email(self):
        url = urljoin(settings.SELF_URL, reverse('barplan'))

        return send_template_email(
            subject=f'Bartendertilmelding: {self.name}',
            body_template='''Hej {name},

Din ansøgning om at blive bartender ved Fredagscaféen er blevet accepteret.
Scheduleren vil tildele dig barvagter, når den nye barplan bliver lavet.
Du kan se barplanen {link}.
Du er blevet tilføjet til vores mailing liste (alle@fredagscafeen.dk).

Ses i baren! :)

/Bestyrelsen''',
            text_format={'name': self.name, 'link': f'her: {url}'},
            html_format={'name': self.name, 'link': mark_safe(f'<a href="{url}">her</a>')},
            to=[self.email],
            cc=['best@fredagscafeen.dk']
        )


    def accept(self):
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


Weekday = IntEnum('Weekday', 'MONDAY TUESDAY WEDNESDAY THURSDAY FRIDAY SATURDAY SUNDAY', start=0)

def next_date_with_weekday(date, weekday):
    date += datetime.timedelta(1)
    while date.weekday() != weekday:
        date += datetime.timedelta(1)

    return date


def next_bartender_shift_start(last_date=None):
    '''
    Returns the next friday after the last shift

    Can't be a class method, because we need to use this as a default value
    '''
    if last_date == None:
        last_shift = BartenderShift.objects.last()
        if last_shift:
            last_date = last_shift.end_datetime.date()
        else:
            last_date = timezone.now().date() - datetime.timedelta(1)

    next_date = next_date_with_weekday(last_date, Weekday.FRIDAY)
    dt = datetime.datetime.combine(next_date, BartenderShift.DEFAULT_START_TIME)
    return timezone.get_default_timezone().localize(dt)


def next_bartender_shift_dates(count):
    d = next_bartender_shift_start().date()
    for i in range(count):
        yield d
        d = next_bartender_shift_start(d).date()


def next_deposit_shift_start(last_date=None):
    '''
    Returns the next monday after the last shift

    Can't be a class method, because we need to use this as a default value
    '''
    if last_date == None:
        last_shift = BoardMemberDepositShift.objects.last()
        if last_shift:
            last_date = last_shift.end_date
        else:
            last_date = timezone.now().date() - datetime.timedelta(1)

    return next_date_with_weekday(last_date, Weekday.MONDAY)


class BartenderShiftPeriod(models.Model):
    generation_datetime = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Generated at {self.generation_datetime}'


class BartenderShift(models.Model):
    # This can't be a timezone aware time because of DST
    DEFAULT_START_TIME = datetime.time(15, 00)
    DEFAULT_SHIFT_DURATION = datetime.timedelta(hours=7)

    start_datetime = models.DateTimeField(default=next_bartender_shift_start)
    end_datetime = models.DateTimeField(blank=True)
    responsible = models.ForeignKey(Bartender, on_delete=models.PROTECT)
    other_bartenders = models.ManyToManyField(Bartender, related_name='shifts', blank=True)

    period = models.ForeignKey(BartenderShiftPeriod, on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        ordering = ('start_datetime', )

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

        return self.objects.exclude(~Q(responsible=bartender),
                                    ~Q(other_bartenders=bartender))

    def is_with_bartender(self, bartender):
        return bartender in self.all_bartenders()

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
        return f'Generated at {self.generation_datetime}'


class BoardMemberDepositShift(models.Model):
    start_date = models.DateField(default=next_deposit_shift_start)
    end_date = models.DateField(blank=True)
    responsibles = models.ManyToManyField(Bartender, related_name='deposit_shifts')

    period = models.ForeignKey(BoardMemberDepositShiftPeriod, on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        ordering = ('start_date', )

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = next_date_with_weekday(self.start_date, Weekday.SUNDAY)

        super().save(*args, **kwargs)

    @classmethod
    def with_bartender(cls, bartender):
        return cls.objects.filter(responsibles=bartender)

    def is_with_bartender(self, bartender):
        return bartender in self.responsibles.all()

    def __str__(self):
        return f'{self.start_date}: {", ".join(b.name for b in self.responsibles.all())}'
