from urllib.parse import urljoin

import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils import timezone
from enum import IntEnum

from .mailman2 import Mailman


class Bartender(models.Model):
    name = models.CharField(max_length=140)
    username = models.CharField(max_length=140, unique=True)
    email = models.CharField(max_length=255, blank=True)
    studentNumber = models.IntegerField(blank=True, null=True)
    phoneNumber = models.IntegerField(blank=True, null=True)
    isActiveBartender = models.BooleanField(default=True)

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


class BoardMember(models.Model):
    bartender = models.OneToOneField(Bartender, on_delete=models.CASCADE, primary_key=True)
    title = models.CharField(max_length=255)
    responsibilities = models.CharField(max_length=255)
    image = models.ImageField(upload_to='boardMembers', blank=True, null=True)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.bartender.username


class BartenderApplication(models.Model):
    name = models.CharField(max_length=140, verbose_name='Navn')
    username = models.CharField(max_length=140, verbose_name='Brugernavn')
    email = models.EmailField(max_length=255)
    studentNumber = models.IntegerField(verbose_name='Studienummer')
    phoneNumber = models.IntegerField(verbose_name='Telefonnummer')
    info = models.TextField(blank=True, help_text='Eventuelle ekstra info til bestyrelsen skrives her')

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created', )

    def _send_accept_email(self):
        barplan_url = urljoin(settings.SELF_URL, reverse('barplan'))
        subject = 'Bartender application: %s' % self.name
        body = 'Hello %s,\n\n' \
                'Your application to become a bartender at Fredagscafeen has been approved.\n' \
                'The scheduler will assign you to shifts which can be found {link},\n' \
                'and you will be added to our mailing list.\n\n' \
                'See you at the bar! :)\n\n' \
                '/Bestyrelsen' % self.name

        body_text = render_to_string('email.txt', {'content': body.format(link='here: %s' % barplan_url)})
        body_html = render_to_string('email.html', {'content': body.format(link=mark_safe('<a href="%s">here</a>' % barplan_url))})

        email = EmailMultiAlternatives(subject=subject, body=body_text, from_email='best@fredagscafeen.dk',
                                       to=[self.email], cc=['best@fredagscafeen.dk'])
        email.attach_alternative(body_html, 'text/html')
        email.send()

    def accept(self):
        b = Bartender.objects.create(name=self.name, username=self.username, email=self.email,
                                     studentNumber=self.studentNumber, phoneNumber=self.phoneNumber)

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
