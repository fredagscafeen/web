from django.conf import settings
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from fredagscafeen.admin_view import custom_admin_view
from printer.views import pdf_preview

from .models import LogBase, LogEntry


@admin.action(description=_("Copy selected logs"))
def copy(self, request, queryset):
    for log in queryset:
        log.pk = None
        log.save()
    self.message_user(
        request,
        ngettext(
            "%d log copied successfully.",
            "%d logs copied successfully.",
            queryset.count(),
        )
        % queryset.count(),
        messages.SUCCESS,
    )


@admin.register(LogBase)
class LogBaseAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "manager",
        "licensee",
        "loan_agreement",
    )
    filter_horizontal = ("key_figures",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    actions = [copy]


class LogEntryContext:
    file_name = "logbog"
    file_path = "log/logbog.tex"

    @staticmethod
    def get_context():
        log_entries = LogEntry.objects.all()
        template_path = settings.MEDIA_ROOT + f"guides/logbog.pdf"
        try:
            with open(template_path, "rb") as f:
                pass
        except FileNotFoundError:
            template_path = None
        return {
            "log_entries": log_entries,
            "template_path": template_path,
        }


@admin.action(description=_("Print selected log entries"))
def printer(self, request, queryset):
    class SelectedLogEntryContext:
        file_name = "logbog"
        file_path = "log/logbog.tex"

        @staticmethod
        def get_context():
            log_entries = queryset
            template_path = settings.MEDIA_ROOT + f"guides/logbog.pdf"
            try:
                with open(template_path, "rb") as f:
                    pass
            except FileNotFoundError:
                template_path = None
            return {
                "log_entries": log_entries,
                "template_path": template_path,
            }

    return pdf_preview(request, self.admin_site, SelectedLogEntryContext)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = (
        "bartender_shift",
        "location",
        "short_description",
    )
    ordering = ("-bartender_shift__start_datetime",)
    date_hierarchy = "bartender_shift__start_datetime"
    actions = [printer]


@custom_admin_view("log", _("Generate logs"))
def generate_log(admin, request):
    return pdf_preview(request, admin.admin_site, LogEntryContext)
