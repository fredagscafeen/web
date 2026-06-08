from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.postgres.fields import ArrayField
from django.db import models
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import ArrayWidget


class CustomModelAdmin(ModelAdmin):
    show_add_link = True
    compressed_fields = True
    warn_unsaved_form = True

    formfield_overrides = {
        # models.TextField: {
        #     "widget": WysiwygWidget,
        # },
        ArrayField: {
            "widget": ArrayWidget,
        },
    }


@admin.register(LogEntry)
class LogEntryAdmin(CustomModelAdmin):
    list_display = (
        "action_time",
        "user",
        "content_type",
        "object_repr",
        "action_flag",
        "change_message",
    )
    list_filter = ("action_flag", "content_type", "user")
    search_fields = ("user__username", "object_repr", "change_message")
    readonly_fields = (
        "action_time",
        "user",
        "content_type",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    )
    date_hierarchy = "action_time"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
