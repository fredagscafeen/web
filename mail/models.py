import datetime
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.db import models
from django.template import Template
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender
from web.models import TimeStampedModel

from .fields import CommaSeparatedEmailField
from .validators import validate_template_syntax


class MailingList(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Navn"))
    isOnlyInternal = models.BooleanField(
        default=False,
        verbose_name=_("Only list members can send to this mailing list"),
    )
    members = models.ManyToManyField(
        Bartender, related_name="mailing_lists", verbose_name=_("Medlemmer")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Mailingliste")
        verbose_name_plural = _("Mailinglister")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    @property
    def count(self):
        return self.members.count()


class EmailTemplate(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=254)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    subject = models.CharField(
        verbose_name=_("Subject"),
        max_length=254,
        blank=False,
        validators=[validate_template_syntax],
    )
    email_html_text = models.TextField(
        verbose_name=_("Email HTML text"),
        blank=True,
        validators=[validate_template_syntax],
    )

    class Meta:
        verbose_name = _("Email template")
        verbose_name_plural = _("Email templates")

    def render_html_text(self, context):
        template = Template(self.email_html_text)
        return template.render(context)

    def render_subject(self, context):
        template = Template(self.subject)
        return template.render(context)

    def __str__(self):
        return self.name


class TemplateVariable(models.Model):
    class Meta:
        verbose_name = _("Template variable")
        verbose_name_plural = _("Template variables")

    email = models.ForeignKey(
        "OutgoingEmail", null=True, blank=True, on_delete=models.CASCADE
    )

    name = models.CharField(
        verbose_name=_("Variable name"), max_length=254, blank=False
    )

    value = models.TextField(verbose_name=_("Variable value"), blank=True)

    def __str__(self):
        return self.name


class OutgoingEmail(models.Model):
    from_mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_("Fra mailingliste"),
        related_name="outgoing_email",
        help_text=f"@{settings.DOMAIN}",
    )
    to = CommaSeparatedEmailField(_("Til email(s)"))
    cc = CommaSeparatedEmailField(_("Cc"))
    bcc = CommaSeparatedEmailField(_("Bcc"))
    reply_to = CommaSeparatedEmailField(_("Svar til"))
    template = models.ForeignKey(
        EmailTemplate,
        verbose_name=_("Template"),
        null=True,
        blank=True,
        help_text=_(
            "If template is selected, HTML message and "
            "subject fields will not be used - they will be populated from template"
        ),
        on_delete=models.CASCADE,
    )
    subject = models.CharField(verbose_name=_("Emne"), max_length=100, blank=True)
    message = models.TextField(verbose_name=_("Besked"), blank=True)
    html_message = models.TextField(
        verbose_name=_("HTML besked"),
        blank=True,
        help_text=_("Used only if template is not selected"),
    )

    class Meta:
        verbose_name = _("Udgående mail")
        verbose_name_plural = _("Udgående mails")

    def __str__(self):
        return self.subject if self.subject else f"Mail ({self.pk})"

    def prepare_email_message(self, to_mails=None):
        """
        Returns a django ``EmailMessage`` or ``EmailMultiAlternatives`` object,
        depending on whether html_message is empty.
        """
        message = self.message
        if self.template is not None:
            _context = self._get_context()
            subject = self.template.render_subject(_context)
            html_message = self.template.render_html_text(_context)
        else:
            subject = self.subject
            html_message = self.html_message

        from_mail = f"{self.from_mailing_list}@{settings.DOMAIN}"
        to_mails = to_mails if to_mails is not None else self.to

        if html_message:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_mail,
                to=to_mails,
                bcc=self.bcc,
                cc=self.cc,
                reply_to=self.reply_to,
            )
            msg.attach_alternative(html_message, "text/html")
        else:
            msg = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_mail,
                to=to_mails,
                bcc=self.bcc,
                cc=self.cc,
                reply_to=self.reply_to,
            )

        for attachment in self.attachments.all():
            msg.attach(
                attachment.name,
                attachment.file.read(),
                mimetype=attachment.mimetype or None,
            )
            attachment.file.close()

        self._cached_email_message = msg
        return msg


def get_attachment_save_path(instance, filename):
    if hasattr(instance, "name"):
        if not instance.name:
            instance.name = filename  # set original filename
    path = "mail_admin_attachments/%Y/%m/%d/"
    if "%" in path:
        path = datetime.datetime.utcnow().strftime(path)

    return os.path.join(
        path,
        filename,
    )


class Attachment(models.Model):
    """
    A model describing an email attachment.
    """

    file = models.FileField(_("File"), upload_to=get_attachment_save_path)
    name = models.CharField(
        _("Name"), max_length=255, help_text=_("The original filename")
    )
    emails = models.ManyToManyField(
        OutgoingEmail, related_name="attachments", blank=True, verbose_name=_("Emails")
    )
    mimetype = models.CharField(max_length=255, default="", blank=True)

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

    def __str__(self):
        return self.name


class MailArchive(TimeStampedModel):
    request_uuid = models.UUIDField(unique=True)
    s3_object_key = models.CharField(max_length=1024)


class IncomingMail(models.Model):
    class Status(models.TextChoices):
        PROCESSED = "PROCESSED", "Processed"
        DROPPED = "DROPPED", "Dropped"

    received_at = models.DateTimeField()
    sender = models.CharField(max_length=320)
    target = models.CharField(max_length=320)
    mailing_list = models.ForeignKey(
        MailingList,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incoming_mails",
    )
    mail_archive = models.OneToOneField(
        MailArchive,
        on_delete=models.CASCADE,
        related_name="incoming_mail",
    )
    status = models.CharField(max_length=9, choices=Status.choices)
    reason = models.TextField(blank=True)


class ForwardedMail(models.Model):
    class Status(models.TextChoices):
        FORWARDED = "FORWARDED", "Forwarded"
        FAILED = "FAILED", "Failed"
        BOUNCED = "BOUNCED", "Bounced"

    incoming_mail = models.ForeignKey(
        IncomingMail,
        on_delete=models.CASCADE,
        related_name="forward_attempts",
    )
    target = models.CharField(max_length=320)
    forwarded_at = models.DateTimeField()
    status = models.CharField(max_length=9, choices=Status.choices)
    reason = models.TextField(blank=True)
    previous_attempt = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="retry_attempts",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(pk=models.F("previous_attempt")),
                name="forwardedmail_previous_attempt_not_self",
            ),
        ]

    def clean(self):
        super().clean()

        if self.previous_attempt_id is None:
            return

        if self.previous_attempt_id == self.pk:
            raise ValidationError(
                {
                    "previous_attempt": _(
                        "A forwarded mail cannot reference itself as previous attempt."
                    )
                }
            )

        previous_attempt = getattr(self, "previous_attempt", None)
        previous_attempt_incoming_mail_id = (
            previous_attempt.incoming_mail_id
            if previous_attempt is not None
            and previous_attempt.pk == self.previous_attempt_id
            else ForwardedMail.objects.filter(pk=self.previous_attempt_id)
            .values_list("incoming_mail_id", flat=True)
            .first()
        )
        if previous_attempt_incoming_mail_id != self.incoming_mail_id:
            raise ValidationError(
                {
                    "previous_attempt": _(
                        "previous_attempt must belong to the same incoming mail."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


def create_attachments(attachment_files):
    """
    Create Attachment instances from files

    attachment_files is a dict of:
        * Key - the filename to be used for the attachment.
        * Value - file-like object, or a filename to open OR a dict of {'file': file-like-object, 'mimetype': string}

    Returns a list of Attachment objects
    """
    attachments = []
    for filename, filedata in attachment_files.items():

        if isinstance(filedata, dict):
            content = filedata.get("file", None)
            mimetype = filedata.get("mimetype", None)
        else:
            content = filedata
            mimetype = None

        opened_file = None

        if isinstance(content, str):
            # `content` is a filename - try to open the file
            opened_file = open(content, "rb")
            content = File(opened_file)

        attachment = Attachment()
        if mimetype:
            attachment.mimetype = mimetype
        attachment.file.save(filename, content=content, save=True)

        attachments.append(attachment)

        if opened_file is not None:
            opened_file.close()

    return attachments


class SpamFilterTLD(models.Model):
    tld = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("TLD"),
        help_text=_(
            "Domain to filter on, supports everything after @ in an email address (e.g. 'example.com' or '.com' to filter all .com domains)"
        ),
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Description"),
        help_text=_(
            "Optional description for the TLD, help the next person understand the purpose of this entry"
        ),
    )
    allowed = models.BooleanField(
        default=False,
        verbose_name=_("Allowed"),
        help_text=_("Whether emails from this TLD should be allowed or blocked"),
    )

    class Meta:
        verbose_name = _("Spam filter TLD")
        verbose_name_plural = _("Spam filter TLDs")

    def __str__(self):
        return self.tld
