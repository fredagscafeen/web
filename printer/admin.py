from django.contrib import admin
from django.db import models
from unfold.widgets import UnfoldAdminSelectWidget

from fredagscafeen.admin import CustomModelAdmin

from .models import Printer


class PrinterSelect(UnfoldAdminSelectWidget):
    def __init__(self, *args, **kwargs):
        kwargs["choices"] = Printer.PrinterChoiceIter()
        super().__init__(*args, **kwargs)


@admin.register(Printer)
class PrinterAdmin(CustomModelAdmin):
    formfield_overrides = {
        **CustomModelAdmin.formfield_overrides,
        models.CharField: {"widget": PrinterSelect},
    }
