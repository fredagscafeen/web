from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe

from fredagscafeen.admin_view import custom_admin_view
from printer.views import pdf_preview

from .models import (
    BeerType,
    Brewery,
    InventoryEntry,
    InventorySnapshot,
    Item,
    Shelf,
    ShelfItem,
)


def filter_by_amount(qs, positive):
    # Slow and hacky solution
    l = []

    for item in qs.all():
        if positive == (item.current_amount > 0):
            l.append(item.id)

    return qs.filter(id__in=l)


class AmountFilter(admin.SimpleListFilter):
    title = "Amount"
    parameter_name = "amount"

    def lookups(self, request, model_admin):
        return [("pos", "> 0"), ("zero", "= 0")]

    def queryset(self, request, queryset):
        value = self.value()
        if value not in ["pos", "zero"]:
            return queryset

        return filter_by_amount(queryset, value == "pos")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "brewery",
        "name",
        "type",
        "container",
        "priceInDKK",
        "inStock",
        "thumbnail",
    )
    search_fields = ("brewery__name", "name")
    list_display_links = ("name", "thumbnail")
    list_filter = (
        AmountFilter,
        "container",
        "type",
        "brewery",
        "glutenFree",
        "nonAlcoholic",
    )
    empty_value_display = ""
    ordering = ("name",)

    ordered_related_fields_to_model = {
        "brewery": Brewery,
        "type": BeerType,
    }

    def thumbnail(self, obj):
        return (
            mark_safe('<img src="%s" width="75px"/>' % obj.image.url)
            if obj.image
            else "<missing>"
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Makes querysets for brewery and type fields ordered by name"""
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

        try:
            model = self.ordered_related_fields_to_model[db_field.name]
            kwargs["queryset"] = model.objects.order_by("name")
        except FieldError:
            pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_search_results(self, request, queryset, search_term):
        """Filter autocomplete to only show in-stock items"""
        queryset, may_have_duplicates = super().get_search_results(
            request, queryset, search_term
        )

        # Only filter for autocomplete requests from ShelfItem inline
        if "autocomplete" in request.path:
            queryset = queryset.filter(inStock=True)

        return queryset, may_have_duplicates


@admin.register(BeerType)
class BeerTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)


@admin.register(Brewery)
class BreweryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)


class InventoryEntryInlineFormSet(forms.models.BaseInlineFormSet):
    model = InventoryEntry

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.id:
            self.initial = []
            for item in filter_by_amount(Item.objects.all(), True):
                self.initial.append(
                    {
                        "amount": item.current_amount,
                        "item": item.id,
                    }
                )

            self.initial.sort(key=lambda x: -x["amount"])

    def save(self):
        super().save()


class InventoryEntryInline(admin.TabularInline):
    model = InventoryEntry
    formset = InventoryEntryInlineFormSet
    fields = ("amount", "item")
    autocomplete_fields = ["item"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return super().get_extra(request, obj, **kwargs)

        return filter_by_amount(Item.objects.all(), True).count() + 1


@admin.register(InventorySnapshot)
class InventoryAdmin(admin.ModelAdmin):
    change_form_template = "admin/enhancedinline.html"
    list_display = ("datetime", "changed_items")
    inlines = [InventoryEntryInline]

    def changed_items(self, obj):
        return obj.entries.count()


class BarMenuContext:
    file_name = "barmenu"
    file_path = "barmenu/barmenu.tex"

    @staticmethod
    def get_context():
        shelves = Shelf.objects.all().prefetch_related(
            "shelf_items__item__brewery", "shelf_items__item__type"
        )

        gluten_free_icon = settings.STATIC_ROOT + "images/no-gluten.png"
        non_alcoholic_icon = settings.STATIC_ROOT + "images/no-alcohol.png"

        return {
            "shelves": shelves,
            "gluten_free_icon": gluten_free_icon,
            "non_alcoholic_icon": non_alcoholic_icon,
        }


@custom_admin_view("items", "generate barmenu")
def generate_bartab(admin, request):
    return pdf_preview(request, admin.admin_site, BarMenuContext)


class ShelfItemInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        """Check that the same item isn't added twice to the shelf"""
        if any(self.errors):
            return

        items = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                item = form.cleaned_data.get("item")
                if item:
                    if item in items:
                        raise ValidationError(
                            f'The item "{item}" is already on this shelf.'
                        )
                    items.append(item)


class ShelfItemInline(admin.TabularInline):
    model = ShelfItem
    formset = ShelfItemInlineFormSet
    extra = 1
    autocomplete_fields = ["item"]
    fields = ("item", "gluten_free_display", "non_alcoholic_display")
    readonly_fields = ("gluten_free_display", "non_alcoholic_display")

    def gluten_free_display(self, obj):
        if obj.item and obj.item.glutenFree:
            return mark_safe('<span style="color: green;">✓ GF</span>')
        return ""

    gluten_free_display.short_description = "Gluten Free"

    def non_alcoholic_display(self, obj):
        if obj.item and obj.item.nonAlcoholic:
            return mark_safe('<span style="color: blue;">✓ NA</span>')
        return ""

    non_alcoholic_display.short_description = "Non-Alcoholic"


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name", "item_count", "items_list")
    inlines = [ShelfItemInline]

    def item_count(self, obj):
        return obj.shelf_items.filter(item__inStock=True).count()

    item_count.short_description = "Items"

    def items_list(self, obj):
        """Display list of items on this shelf with links"""
        shelf_items = (
            obj.shelf_items.filter(item__inStock=True)
            .select_related("item", "item__brewery")
            .order_by("order", "item__name")
        )

        if not shelf_items:
            return "-"

        links = []
        for si in shelf_items:
            url = reverse("admin:items_item_change", args=[si.item.id])
            links.append(f'<li><a href="{url}">{si.item}</a></li>')

        return mark_safe(f'<ul>{"".join(links)}</ul>')

    items_list.short_description = "Items on Shelf"
