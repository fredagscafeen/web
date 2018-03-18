from urllib.parse import urljoin

import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.urls import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils import timezone
from enum import IntEnum


class Bartender(models.Model):
    name = models.CharField(max_length=140)
    username = models.CharField(max_length=140)
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
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} ({self.username})'


class BoardMember(models.Model):
    bartender = models.OneToOneField(Bartender, on_delete=models.CASCADE, primary_key=True)
    title = models.CharField(max_length=255)
    responsibilities = models.CharField(max_length=255)
    image = models.ImageField(upload_to='boardMembers', blank=True, null=True)

    def __str__(self):
        return self.bartender.username


class BartenderApplication(models.Model):
    name = models.CharField(max_length=140, verbose_name='Navn')
    username = models.CharField(max_length=140, verbose_name='Brugernavn', help_text='Brug evt. NFIT')
    email = models.EmailField(max_length=255)
    studentNumber = models.IntegerField(verbose_name='Studienummer')
    phoneNumber = models.IntegerField(verbose_name='Telefonnummer')
    info = models.TextField(blank=True, help_text='Eventuelle ekstra info til bestyrelsen skrives her')

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created', )

    def accept(self):
        b = Bartender.objects.create(name=self.name, username=self.username, email=self.email,
                                     studentNumber=self.studentNumber, phoneNumber=self.phoneNumber)

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

        return b.pk

    def __str__(self):
        return self.username


Weekday = IntEnum('Weekday', 'MONDAY TUESDAY WEDNESDAY THURSDAY FRIDAY SATURDAY SUNDAY', start=0)

def next_date_with_weekday(date, weekday):
    date += datetime.timedelta(1)
    while date.weekday() != weekday:
        date += datetime.timedelta(1)

    return date


def next_bartender_shift_start():
    '''
    Returns the next friday after the last shift

    Can't be a class method, because we need to use this as a default value
    '''
    last_shift = BartenderShift.objects.last()
    if last_shift:
        last_date = last_shift.end_datetime.date()
    else:
        last_date = timezone.now().date() - datetime.timedelta(1)

    next_date = next_date_with_weekday(last_date, Weekday.FRIDAY)
    return datetime.datetime.combine(next_date, BartenderShift.DEFAULT_START_TIME)


def next_deposit_shift_start():
    '''
    Returns the next monday after the last shift

    Can't be a class method, because we need to use this as a default value
    '''
    last_shift = BoardMemberDepositShift.objects.last()
    if last_shift:
        last_date = last_shift.end_date
    else:
        last_date = timezone.now().date() - datetime.timedelta(1)

    return next_date_with_weekday(last_date, Weekday.MONDAY)


class BartenderShift(models.Model):
    DEFAULT_START_TIME = datetime.time(15, 00, tzinfo=timezone.get_current_timezone())
    DEFAUlT_END_TIME = datetime.time(22, 00, tzinfo=timezone.get_current_timezone())

    start_datetime = models.DateTimeField(default=next_bartender_shift_start)
    end_datetime = models.DateTimeField(blank=True)
    responsible = models.ForeignKey(Bartender, on_delete=models.PROTECT, limit_choices_to={'boardmember__isnull': False})
    other_bartenders = models.ManyToManyField(Bartender, limit_choices_to={'isActiveBartender': True}, related_name='shifts', blank=True)

    class Meta:
        ordering = ('start_datetime', )

    def clean(self):
        if not self.end_datetime:
            start_date = self.start_datetime.date()
            start_time = self.start_datetime.time()
            if start_time != self.DEFAULT_START_TIME:
                return ValidationError('You must provide end time, if start time is not at 15:00')

            self.end_datetime = datetime.datetime.combine(start_date, self.DEFAUlT_END_TIME)

    def all_bartenders(self):
        return [self.responsible] + list(self.other_bartenders.all())

    @classmethod
    def with_bartender(self, username):
        # You can't use filter as it returns multiple of the same object:
        # return self.objects.filter(Q(responsible__username=username) | Q(other_bartenders__username=username))

        return self.objects.exclude(~Q(responsible__username=username),
                                    ~Q(other_bartenders__username=username))

    @property
    def date(self):
        return self.start_datetime.date()

    def __str__(self):
        return f'{self.date}: Responsible: {self.responsible.name}, Other bartenders: {", ".join(b.name for b in self.other_bartenders.all())}'


class BoardMemberDepositShift(models.Model):
    start_date = models.DateField(default=next_deposit_shift_start)
    end_date = models.DateField(blank=True)
    responsibles = models.ManyToManyField(Bartender, limit_choices_to={'boardmember__isnull': False}, related_name='deposit_shifts')

    class Meta:
        ordering = ('start_date', )

    def clean(self):
        if not self.end_date:
            self.end_date = next_date_with_weekday(self.start_date, Weekday.SUNDAY)

    @classmethod
    def with_bartender(cls, username):
        return cls.objects.filter(responsibles__username=username)

    def __str__(self):
        return f'{self.start_date}: {", ".join(b.name for b in self.responsibles.all())}'
