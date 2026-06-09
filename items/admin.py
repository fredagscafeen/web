from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline

from fredagscafeen.admin import CustomModelAdmin
from fredagscafeen.admin_view import custom_admin_view
from printer.views import pdf_preview

from .models import (
    BeerType,
    Brewery,
    Fridge,
    FridgeShelfAssignment,
    InventoryEntry,
    InventorySnapshot,
    Item,
    Shelf,
    ShelfItem,
)
from .shelf_labels import build_shelf_label_context


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


class FridgeShelfInline(TabularInline):
    model = FridgeShelfAssignment
    fields = ("shelf", "order", "item_count", "items_list")
    readonly_fields = ("item_count", "items_list")
    autocomplete_fields = ["shelf"]
    extra = 0
    ordering_field = "order"
    hide_ordering_field = True

    def item_count(self, obj):
        if not obj.shelf_id:
            return 0
        return obj.shelf.shelf_items.filter(item__inStock=True).count()

    item_count.short_description = "Items"

    def items_list(self, obj):
        if not obj.shelf_id:
            return "-"
        shelf_items = (
            obj.shelf.shelf_items.filter(item__inStock=True)
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


@admin.register(Fridge)
class FridgeAdmin(CustomModelAdmin):
    list_display = (
        "name",
        "shelves_count",
        "shelves_list",
    )
    search_fields = ("name",)
    inlines = [FridgeShelfInline]
    fields = ("name",)
    ordering_field = "order"
    hide_ordering_field = True

    def shelves_count(self, obj):
        return obj.shelf_assignments.count()

    shelves_count.short_description = "Shelves"

    def shelves_list(self, obj):
        """Display list of shelves on this fridge with links"""
        shelf_assignments = obj.shelf_assignments.select_related("shelf").order_by(
            "order"
        )

        if not shelf_assignments:
            return "-"

        links = []
        for sa in shelf_assignments:
            url = reverse("admin:items_shelf_change", args=[sa.shelf.id])
            links.append(f'<li><a href="{url}">{sa.shelf.name}</a></li>')

        return mark_safe(f'<ul>{"".join(links)}</ul>')

    shelves_list.short_description = "Shelves"


@admin.register(Item)
class ItemAdmin(CustomModelAdmin):
    list_display = (
        "brewery",
        "name",
        "type",
        "container",
        "priceInDKK",
        "bestBefore",
        "inStock",
        "thumbnail",
    )
    search_fields = ("brewery__name", "name")
    list_display_links = ("name", "thumbnail")
    list_filter = (
        AmountFilter,
        "bestBefore",
        "container",
        "type",
        "brewery",
        "glutenFree",
        "nonAlcoholic",
    )
    empty_value_display = ""
    ordering = ("name",)
    actions = ["print_shelf_labels"]
    autocomplete_fields = ["brewery", "type"]

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

    @admin.action(description="Print shelf labels for selected items")
    def print_shelf_labels(self, request, queryset):
        class SelectedShelfLabelContext:
            file_name = "shelf_labels"
            file_path = "shelf_labels/shelf_labels.tex"

            @staticmethod
            def get_context_for_work_dir(work_dir):
                items = queryset.select_related("brewery", "type").order_by("name")
                return build_shelf_label_context(
                    [{"item": item} for item in items], work_dir
                )

        request.method = "GET"
        return pdf_preview(request, self.admin_site, SelectedShelfLabelContext)


@admin.register(BeerType)
class BeerTypeAdmin(CustomModelAdmin):
    list_display = (
        "name",
        "link",
    )
    ordering = ("name",)
    search_fields = ("name",)


@admin.register(Brewery)
class BreweryAdmin(CustomModelAdmin):
    list_display = (
        "name",
        "website",
    )
    ordering = ("name",)
    search_fields = ("name",)


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


class InventoryEntryInline(TabularInline):
    model = InventoryEntry
    formset = InventoryEntryInlineFormSet
    fields = ("amount", "item")
    autocomplete_fields = ["item"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return super().get_extra(request, obj, **kwargs)

        return filter_by_amount(Item.objects.all(), True).count() + 1


@admin.register(InventorySnapshot)
class InventoryAdmin(CustomModelAdmin):
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


class ShelfLabelContext:
    file_name = "shelf_labels"
    file_path = "shelf_labels/shelf_labels.tex"

    @staticmethod
    def get_context_for_work_dir(work_dir):
        label_items = (
            ShelfItem.objects.select_related(
                "item", "item__brewery", "item__type", "shelf"
            )
            .prefetch_related("shelf__fridge_assignments__fridge")
            .order_by(
                "shelf__fridge_assignments__fridge__name",
                "shelf__name",
                "order",
                "item__name",
            )
        )

        return build_shelf_label_context(label_items, work_dir)


@custom_admin_view("items", "generate shelf labels")
def generate_shelf_labels(admin, request):
    return pdf_preview(request, admin.admin_site, ShelfLabelContext)


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


class ShelfItemInline(TabularInline):
    model = ShelfItem
    formset = ShelfItemInlineFormSet
    extra = 0
    autocomplete_fields = ["item"]
    fields = (
        "item",
        "item_image",
        "gluten_free_display",
        "non_alcoholic_display",
        "order",
    )
    readonly_fields = ("gluten_free_display", "non_alcoholic_display", "item_image")
    ordering_field = "order"
    hide_ordering_field = True

    def item_image(self, obj):
        if obj.item and obj.item.image:
            return format_html(
                '<img src="{}" style="max-height: 48px; border-radius: 4px;" />',
                obj.item.image.url,
            )
        return ""

    item_image.short_description = "Image"

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


class ShelfFridgeInline(TabularInline):
    model = FridgeShelfAssignment
    fields = ("fridge",)
    autocomplete_fields = ["fridge"]
    extra = 1
    max_num = 1


class FridgeFilter(admin.SimpleListFilter):
    title = "Fridge"
    parameter_name = "fridge"

    def lookups(self, request, model_admin):
        return [(f.id, f.name) for f in Fridge.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fridge_assignments__fridge_id=self.value())
        return queryset


@admin.register(Shelf)
class ShelfAdmin(CustomModelAdmin):
    list_display = ("name", "fridge", "item_count", "items_list")
    list_filter = (FridgeFilter,)
    inlines = [ShelfFridgeInline, ShelfItemInline]
    search_fields = ("name",)
    fields = ("name",)

    def get_queryset(self, request):
        return (
            super().get_queryset(request).prefetch_related("fridge_assignments__fridge")
        )

    def fridge(self, obj):
        assignment = next(iter(obj.fridge_assignments.all()), None)
        if not assignment:
            return "-"
        url = reverse("admin:items_fridge_change", args=[assignment.fridge.id])
        return mark_safe(f'<a href="{url}">{assignment.fridge.name}</a>')

    fridge.short_description = "Fridge"
    fridge.admin_order_field = "fridge_assignments__fridge__name"

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
