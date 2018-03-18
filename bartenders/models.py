from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


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
        return self.name


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

class BartenderShift(models.Model):
    date = models.DateField()
    responsible = models.ForeignKey(Bartender, on_delete=models.PROTECT, limit_choices_to={'boardmember__isnull': False})
    bartenders = models.ManyToManyField(Bartender, limit_choices_to={'isActiveBartender': True}, related_name='Bartenders')

    class Meta:
        ordering = ('date', )

class BoardMemberDepositShift(models.Model):
    date = models.DateField()
    responsible = models.ManyToManyField(Bartender, limit_choices_to={'boardmember__isnull': False})

    class Meta:
        ordering = ('date', )
