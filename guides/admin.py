from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Guide


@admin.register(Guide)
class GuideAdmin(ModelAdmin):
    list_display = (
        "name",
        "category",
        "updated_at",
    )
