from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import model_to_dict
from django.utils.safestring import mark_safe


class Bartender(models.Model):
    name = models.CharField(max_length=140)
    username = models.CharField(max_length=140)
    email = models.CharField(max_length=255, blank=True, null=True)
    studentNumber = models.IntegerField(blank=True, null=True)
    phoneNumber = models.IntegerField(blank=True, null=True)
    isActiveBartender = models.BooleanField(default=True)
    isBoardMember = models.BooleanField(default=False)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.username


class BoardMember(models.Model):
    bartender = models.ForeignKey(Bartender, null=False, blank=False)
    title = models.CharField(max_length=255)
    responsibilities = models.CharField(max_length=255)

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

        subject = 'Bartender application: %s' % self.name
        body = 'Hello %s,\n\n' \
                'Your application to become a bartender at Fredagscafeen has been approved.\n' \
                'The scheduler will assign you to shifts which can be found %s,\n' \
                'and you will be added to our mailing list.\n\n' \
                'See you at the bar! :)\n\n' \
                '/Bestyrelsen' % (self.name, mark_safe('<a href="%s">here</a>' % urljoin(settings.SELF_URL, reverse('barplan'))))

        email = EmailMessage(subject=subject, body=body, from_email='best@fredagscafeen.dk',
                             to=[self.email], cc=['best@fredagscafeen.dk'])
        email.send()

        return b.pk

    def __str__(self):
        return self.username
