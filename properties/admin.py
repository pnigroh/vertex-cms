import json

from django import forms
from django.contrib import admin
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from parler.admin import TranslatableAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin

from .models import (
    Location, AmenityCategory, Amenity, PropertyStatus, Property, PropertyImage,
)


class PropertyImageForm(forms.ModelForm):
    """Custom form that treats rows with no image file as empty.

    adminsortable2 pre-fills ``order`` and Django pre-fills the FK
    ``property`` on every extra row.  This makes Django's formset think
    the row has data even when the user left it blank, which triggers a
    "This field is required" error on the ``image`` field.

    We override ``has_changed`` so that a row with only the auto-filled
    ``order`` and ``property`` values is still considered empty.
    """

    class Meta:
        model = PropertyImage
        fields = "__all__"

    def has_changed(self):
        if not self.instance.pk and not self.files.get(self.add_prefix("image")):
            return False
        return super().has_changed()


# ═══════════════════════════════════════════════════════════════════════════
# Location (tree)
# ═══════════════════════════════════════════════════════════════════════════
@admin.register(Location)
class LocationAdmin(TreeAdmin):
    form = movenodeform_factory(Location)
    list_display = ("name", "location_type", "slug")
    list_filter = ("location_type",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


# ═══════════════════════════════════════════════════════════════════════════
# Amenities
# ═══════════════════════════════════════════════════════════════════════════
class AmenityInline(admin.TabularInline):
    model = Amenity
    extra = 1
    fields = ("name", "icon", "order")
    ordering = ("order", "name")


@admin.register(AmenityCategory)
class AmenityCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "amenity_count")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AmenityInline]

    @admin.display(description=_("# amenities"))
    def amenity_count(self, obj):
        return obj.amenities.count()


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "icon", "order")
    list_filter = ("category",)
    list_editable = ("order",)
    search_fields = ("name",)


# ═══════════════════════════════════════════════════════════════════════════
# Property status
# ═══════════════════════════════════════════════════════════════════════════
@admin.register(PropertyStatus)
class PropertyStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_published_status", "property_count")
    list_editable = ("order", "is_published_status")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    @admin.display(description=_("# properties"))
    def property_count(self, obj):
        return obj.properties.count()


# ═══════════════════════════════════════════════════════════════════════════
# Property images (sortable inline)
# ═══════════════════════════════════════════════════════════════════════════
class PropertyImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = PropertyImage
    form = PropertyImageForm
    extra = 1
    fields = ("order", "image", "alt_text", "is_cover", "thumbnail_preview")
    readonly_fields = ("thumbnail_preview",)

    class Media:
        js = ("properties/admin/js/bulk_upload.js",)

    @admin.display(description=_("preview"))
    def thumbnail_preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-height:60px;max-width:100px;'
                'object-fit:cover;border-radius:4px;" />',
                obj.image.url,
            )
        return "-"


# ═══════════════════════════════════════════════════════════════════════════
# Property (translatable)
# ═══════════════════════════════════════════════════════════════════════════
@admin.register(Property)
class PropertyAdmin(SortableAdminBase, TranslatableAdmin):
    # Override parler's dynamic template so we control the full layout.
    # Language tabs are included manually inside the Details tab panel.
    change_form_template = "admin/properties/property/change_form.html"

    def get_language_tabs(self, request, obj, available_languages, css_class=None):
        tabs = super().get_language_tabs(request, obj, available_languages, css_class=css_class)
        tabs.allow_deletion = False
        return tabs

    # --- List view ---------------------------------------------------------
    list_display = (
        "title_column",
        "property_type",
        "listing_type",
        "location",
        "sale_price",
        "rental_price",
        "status",
        "is_featured",
        "cover_thumbnail",
    )
    list_filter = (
        "property_type",
        "listing_type",
        "status",
        "is_featured",
        "currency",
    )
    search_fields = ("translations__title", "translations__description")
    list_editable = ("is_featured",)

    # --- Form layout -------------------------------------------------------
    fieldsets = (
        (_("General (translated)"), {
            "fields": ("title", "slug", "description"),
            "description": _("Use the language tabs above to provide translations."),
        }),
        (_("Classification"), {
            "fields": ("property_type", "listing_type"),
        }),
        (_("Specifications"), {
            "fields": (
                ("bedrooms", "bathrooms", "parking_spaces"),
                ("construction_area", "lot_area"),
                "year_built",
            ),
        }),
        (_("Pricing"), {
            "fields": (("sale_price", "rental_price", "currency"),),
        }),
        (_("Location"), {
            "fields": ("location",),
        }),
        (_("Amenities"), {
            "fields": ("amenities",),
        }),
        (_("Status"), {
            "fields": (("status", "is_featured"),),
        }),
        (_("Timestamps"), {
            "fields": (("created_at", "updated_at"),),
        }),
    )
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("amenities",)
    inlines = [PropertyImageInline]

    def get_prepopulated_fields(self, request, obj=None):
        return {"slug": ("title",)}

    # --- Custom columns ----------------------------------------------------
    @admin.display(description=_("title"))
    def title_column(self, obj):
        return obj.safe_translation_getter("title", any_language=True) or "-"

    @admin.display(description=_("cover"))
    def cover_thumbnail(self, obj):
        cover = obj.cover_image
        if cover and cover.image:
            return format_html(
                '<img src="{}" style="max-height:50px;max-width:80px;'
                'object-fit:cover;border-radius:4px;" />',
                cover.image.url,
            )
        return "-"

    # --- Custom URLs for bulk image upload ---------------------------------
    def get_urls(self):
        custom = [
            path(
                "<int:property_id>/upload-images/",
                self.admin_site.admin_view(self.upload_images_view),
                name="properties_property_upload_images",
            ),
        ]
        return custom + super().get_urls()

    def upload_images_view(self, request, property_id):
        """Handle the popup multi-image upload.

        GET  → render the upload popup template
        POST → accept uploaded files, create PropertyImage records, return JSON
        """
        prop = get_object_or_404(Property, pk=property_id)

        if not self.has_change_permission(request, prop):
            return JsonResponse({"error": "Permission denied"}, status=403)

        if request.method == "POST":
            files = request.FILES.getlist("images")
            if not files:
                return JsonResponse({"error": "No files provided"}, status=400)

            # Determine starting order value
            max_order = (
                PropertyImage.objects.filter(property=prop)
                .aggregate(m=Max("order"))["m"]
            )
            next_order = (max_order or 0) + 1

            created = []
            errors = []
            for i, f in enumerate(files):
                # Basic validation
                if not f.content_type.startswith("image/"):
                    errors.append({"name": f.name, "error": "Not an image file"})
                    continue
                if f.size > 10 * 1024 * 1024:  # 10 MB limit
                    errors.append({"name": f.name, "error": "File too large (max 10 MB)"})
                    continue

                try:
                    pi = PropertyImage(
                        property=prop,
                        alt_text="",
                        is_cover=False,
                        order=next_order + i,
                    )
                    pi.image.save(f.name, f, save=True)
                    created.append({
                        "id": pi.pk,
                        "name": f.name,
                        "url": pi.image.url,
                        "order": pi.order,
                    })
                except Exception as e:
                    errors.append({"name": f.name, "error": str(e)})

            return JsonResponse({
                "created": created,
                "errors": errors,
                "total_created": len(created),
                "total_errors": len(errors),
            })

        # GET → render popup
        context = {
            **self.admin_site.each_context(request),
            "property": prop,
            "title": f"Upload images — {prop}",
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/properties/upload_images_popup.html",
            context,
        )
