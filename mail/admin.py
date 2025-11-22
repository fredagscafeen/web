from django.conf import settings
from django.contrib import admin, messages
from django.forms.widgets import TextInput
from django.http import HttpResponse
from django.shortcuts import reverse
from django.template import Context
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_object_actions import DjangoObjectActions

from .fields import CommaSeparatedEmailField
from .forms import OutgoingEmailAdminForm
from .models import (
    Attachment,
    EmailTemplate,
    MailingList,
    OutgoingEmail,
    TemplateVariable,
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
            f"{subject} mail sendt.",
            messages.SUCCESS,
        )

    def send_test(self, request, obj):
        mail = obj.prepare_email_message(request.user.email)
        mail.send()
        subject = mail.subject if mail.subject else "'<missing>'"
        self.message_user(
            request,
            f"{subject} test mail sendt til {request.user.email}.",
            messages.SUCCESS,
        )
