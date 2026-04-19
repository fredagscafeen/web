from django.contrib import admin

from fredagscafeen.models import CustomModelAdmin

from .models import Guide


@admin.register(Guide)
class GuideAdmin(CustomModelAdmin):
    list_display = (
        "name",
        "category",
        "updated_at",
    )
