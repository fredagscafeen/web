from urllib import request

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Count, Exists, OuterRef, Q
from django.forms.widgets import TextInput
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import reverse
from django.template import Context
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_object_actions import DjangoObjectActions

from .fields import CommaSeparatedEmailField
from .forms import OutgoingEmailAdminForm
from .models import (
    Attachment,
    EmailTemplate,
    ForwardedMail,
    IncomingMail,
    MailingList,
    OutgoingEmail,
    SpamFilterTLD,
    TemplateVariable,
)
from .services import (
    RETRYABLE_FORWARDED_STATUSES,
    build_mail_archive_download_url,
    get_retryable_forwarded_mails,
    request_forwarded_mail_resend,
)


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    list_display = ("name", "count", "isOnlyInternal")
    filter_horizontal = ("members",)


admin.site.register(EmailTemplate)


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "subject")
    readonly_fields = ["preview_template_field"]

    def preview_template_field(self, o):
        if o.id:
            url = reverse(
                "admin:django_mail_admin_emailtemplate_change",
                kwargs={"object_id": o.pk},
            )
            url = url + "?preview_template=true"
            return mark_safe(
                f'<a href="{url}" target="_blank">Preview this template</a>'
            )
        else:
            return "---"

    preview_template_field.short_description = "Preview"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.GET.get("preview_template", "").lower() == "true":
            return self.preview_template_view(request, object_id)
        return super().change_view(request, object_id, form_url, extra_context)

    def preview_template_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        content = obj.render_html_text(Context())
        return HttpResponse(content, content_type="text/html")


class TemplateVariableInline(admin.TabularInline):
    model = TemplateVariable
    extra = 1


class AttachmentInline(admin.TabularInline):
    model = Attachment.emails.through
    extra = 1
    verbose_name = _("Attachment")
    verbose_name_plural = _("Attachments")


admin.site.register(Attachment)


class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "file",
    )


class CommaSeparatedEmailWidget(TextInput):
    def __init__(self, *args, **kwargs):
        super(CommaSeparatedEmailWidget, self).__init__(*args, **kwargs)
        self.attrs.update({"class": "vTextField"})

    def format_value(self, value):
        # If the value is a string wrap it in a list so it does not get sliced.
        if not value:
            return ""
        if isinstance(value, str):
            value = [
                value,
            ]
        return ", ".join([item for item in value])


class ForwardedMailInline(admin.TabularInline):
    model = ForwardedMail
    extra = 0
    can_delete = False
    show_change_link = True
    fields = (
        "target",
        "status",
        "forwarded_at",
        "reason",
        "previous_attempt",
        "resend_link",
    )
    readonly_fields = fields
    ordering = ("forwarded_at", "pk")

    def resend_link(self, obj):
        if not obj.pk or obj.status not in RETRYABLE_FORWARDED_STATUSES:
            return "---"

        url = reverse(
            "admin:mail_forwardedmail_actions",
            kwargs={"pk": obj.pk, "tool": "resend"},
        )
        return format_html('<a href="{}">Resend</a>', url)

    resend_link.short_description = _("Resend")


@admin.action(description=_("Block selected domains"))
def incoming_mail_block_domains(modeladmin, request, queryset):
    sender_domains = set(
        mail.sender.split("@")[-1]
        .lower()
        .split(":")[0]
        .strip("[]")
        .strip(">")
        .strip("<")
        for mail in queryset
        if mail.sender
    )
    existing_tlds = set(
        SpamFilterTLD.objects.filter(tld__in=sender_domains).values_list(
            "tld", flat=True
        )
    )
    new_tlds = sender_domains - existing_tlds

    SpamFilterTLD.objects.bulk_create(
        [SpamFilterTLD(tld=tld, allowed=False) for tld in new_tlds]
    )

    updated_count = SpamFilterTLD.objects.filter(tld__in=sender_domains).update(
        allowed=False
    )

    modeladmin.message_user(
        request,
        f"{updated_count} domain(s) have been blocked in the spam filter.",
        messages.SUCCESS,
    )


@admin.register(IncomingMail)
class IncomingMailAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = (
        "received_at",
        "sender",
        "target",
        "mailing_list",
        "status",
        "current_forwarded_count_display",
        "current_failed_count_display",
        "current_bounced_count_display",
        "has_resends_display",
    )
    list_filter = ("status", "mailing_list")
    list_select_related = ("mail_archive", "mailing_list")
    ordering = ("-received_at",)
    readonly_fields = (
        "received_at",
        "sender",
        "target",
        "mailing_list",
        "status",
        "reason",
        "mail_archive_link",
        "current_forwarded_count_display",
        "current_failed_count_display",
        "current_bounced_count_display",
        "has_resends_display",
    )
    fields = readonly_fields
    inlines = (ForwardedMailInline,)
    change_actions = ("download_eml", "resend", "block_in_spamfilter")
    actions = [incoming_mail_block_domains]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("mail_archive", "mailing_list")
            .annotate(
                current_forwarded_count=Count(
                    "forward_attempts",
                    filter=Q(forward_attempts__retry_attempts__isnull=True)
                    & Q(forward_attempts__status=ForwardedMail.Status.FORWARDED),
                ),
                current_failed_count=Count(
                    "forward_attempts",
                    filter=Q(forward_attempts__retry_attempts__isnull=True)
                    & Q(forward_attempts__status=ForwardedMail.Status.FAILED),
                ),
                current_bounced_count=Count(
                    "forward_attempts",
                    filter=Q(forward_attempts__retry_attempts__isnull=True)
                    & Q(forward_attempts__status=ForwardedMail.Status.BOUNCED),
                ),
                has_resends=Exists(
                    ForwardedMail.objects.filter(
                        incoming_mail_id=OuterRef("pk"),
                        previous_attempt__isnull=False,
                    )
                ),
            )
        )

    def _get_delivery_count(self, obj, attribute_name, status):
        annotated_value = getattr(obj, attribute_name, None)
        if annotated_value is not None:
            return annotated_value
        return obj.forward_attempts.filter(
            retry_attempts__isnull=True,
            status=status,
        ).count()

    def current_forwarded_count_display(self, obj):
        return self._get_delivery_count(
            obj,
            "current_forwarded_count",
            ForwardedMail.Status.FORWARDED,
        )

    current_forwarded_count_display.short_description = _("Forwarded")

    def current_failed_count_display(self, obj):
        return self._get_delivery_count(
            obj,
            "current_failed_count",
            ForwardedMail.Status.FAILED,
        )

    current_failed_count_display.short_description = _("Failed")

    def current_bounced_count_display(self, obj):
        return self._get_delivery_count(
            obj,
            "current_bounced_count",
            ForwardedMail.Status.BOUNCED,
        )

    current_bounced_count_display.short_description = _("Bounced")

    def has_resends_display(self, obj):
        annotated_value = getattr(obj, "has_resends", None)
        if annotated_value is not None:
            return annotated_value
        return obj.forward_attempts.filter(previous_attempt__isnull=False).exists()

    has_resends_display.short_description = _("Has resends")
    has_resends_display.boolean = True

    def mail_archive_link(self, obj):
        if not obj.pk:
            return "---"

        url = reverse(
            "admin:mail_incomingmail_actions",
            kwargs={"pk": obj.pk, "tool": "download_eml"},
        )
        return format_html('<a href="{}" download>Download EML</a>', url)

    mail_archive_link.short_description = _("Archive")

    def download_eml(self, request, obj):
        try:
            download_url = build_mail_archive_download_url(obj.mail_archive)
        except Exception as error:
            self.message_user(request, str(error), messages.ERROR)
            return HttpResponseRedirect(
                reverse("admin:mail_incomingmail_change", args=[obj.pk])
            )

        return HttpResponseRedirect(download_url)

    download_eml.label = _("Download EML")

    def resend(self, request, obj):
        retryable_attempts = list(
            get_retryable_forwarded_mails(obj)
            .select_related("incoming_mail__mail_archive")
            .order_by("forwarded_at", "pk")
        )

        if not retryable_attempts:
            self.message_user(
                request, _("No failed recipients to resend."), messages.WARNING
            )
            return

        success_count = 0
        errors = []
        for forwarded_mail in retryable_attempts:
            try:
                request_forwarded_mail_resend(forwarded_mail)
            except Exception as error:
                errors.append(str(error))
            else:
                success_count += 1

        if success_count:
            self.message_user(
                request,
                _("Queued resend for %(count)s recipient(s).")
                % {"count": success_count},
                messages.SUCCESS,
            )

        if errors:
            self.message_user(request, "; ".join(errors), messages.ERROR)
            return

    resend.label = _("Resend failed recipients")

    def block_in_spamfilter(self, request, obj):
        sender_domain = (
            obj.sender.split("@")[-1]
            .lower()
            .split(":")[0]
            .strip("[]")
            .strip(">")
            .strip("<")
        )
        spam_filter_entry, created = SpamFilterTLD.objects.get_or_create(
            tld=sender_domain
        )
        if not created and not spam_filter_entry.allowed:
            self.message_user(
                request,
                _("TLD '%(tld)s' is already blocked in the spam filter.")
                % {"tld": sender_domain},
                messages.INFO,
            )
            return

        spam_filter_entry.allowed = False
        spam_filter_entry.save()

        self.message_user(
            request,
            _("TLD '%(tld)s' has been blocked in the spam filter.")
            % {"tld": sender_domain},
            messages.SUCCESS,
        )

    block_in_spamfilter.label = _("Block sender's Domain in spam filter")


@admin.register(ForwardedMail)
class ForwardedMailAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = (
        "incoming_mail",
        "target",
        "status",
        "forwarded_at",
        "previous_attempt",
    )
    list_filter = ("status",)
    list_select_related = (
        "incoming_mail",
        "previous_attempt",
        "incoming_mail__mail_archive",
    )
    readonly_fields = list_display + ("reason",)
    fields = readonly_fields
    ordering = ("-forwarded_at",)
    change_actions = ("resend",)

    def get_change_actions(self, request, object_id, form_url):
        actions = super().get_change_actions(request, object_id, form_url)
        obj = self.get_object(request, object_id)
        if obj is None or obj.status not in RETRYABLE_FORWARDED_STATUSES:
            return tuple(action for action in actions if action != "resend")
        return actions

    def resend(self, request, obj):
        try:
            request_forwarded_mail_resend(obj)
        except Exception as error:
            self.message_user(request, str(error), messages.ERROR)
            return

        self.message_user(
            request,
            _("Queued resend for %(target)s.") % {"target": obj.target},
            messages.SUCCESS,
        )

    resend.label = _("Resend")


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = [
        "subject_display",
        "from_mailing_list_display",
        "to_display",
        "template",
    ]
    inlines = [TemplateVariableInline]
    formfield_overrides = {
        CommaSeparatedEmailField: {"widget": CommaSeparatedEmailWidget}
    }
    form = OutgoingEmailAdminForm

    def from_mailing_list_display(self, instance):
        return f"{instance.from_mailing_list}@{settings.DOMAIN}"

    from_mailing_list_display.short_description = _("Fra email")

    def to_display(self, instance):
        return ", ".join(instance.to) if instance.to else "<missing>"

    to_display.short_description = _("Til email(s)")

    def subject_display(self, instance):
        return instance.subject if instance.subject else "<missing>"

    subject_display.short_description = _("Emne")

    change_actions = ("send", "send_test")

    def send(self, request, obj):
        mail = obj.prepare_email_message()
        mail.send()
        subject = mail.subject if mail.subject else "'<missing>'"
        self.message_user(
            request,
            f"'{subject}' mail sendt.",
            messages.SUCCESS,
        )

    def send_test(self, request, obj):
        to_mails = [request.user.email]
        mail = obj.prepare_email_message(to_mails)
        mail.send()
        subject = mail.subject if mail.subject else "'<missing>'"
        self.message_user(
            request,
            f"'{subject}' test mail sendt til {request.user.email}.",
            messages.SUCCESS,
        )


@admin.action(description=_("Allow selected TLDs"))
def allow_tlds(modeladmin, request, queryset):
    updated_count = queryset.update(allowed=True)
    modeladmin.message_user(
        request,
        f"{updated_count} TLD(s) have been allowed.",
        messages.SUCCESS,
    )


@admin.action(description=_("Block selected TLDs"))
def block_tlds(modeladmin, request, queryset):
    updated_count = queryset.update(allowed=False)
    modeladmin.message_user(
        request,
        f"{updated_count} TLD(s) have been blocked.",
        messages.SUCCESS,
    )


@admin.register(SpamFilterTLD)
class SpamFilterTLDAdmin(admin.ModelAdmin):
    list_display = (
        "allowed",
        "tld",
        "description",
    )
    list_filter = ("allowed",)
    list_display_links = ("tld",)
    ordering = ("-allowed",)
    actions = [allow_tlds, block_tlds]
