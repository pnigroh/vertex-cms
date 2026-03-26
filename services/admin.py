from django.contrib import admin
from django.utils.html import format_html
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "thumbnail_preview", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "intro", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "thumbnail_preview")
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "is_published"),
        }),
        ("Content", {
            "fields": ("intro", "content", "image", "thumbnail_preview"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:80px; border-radius:4px;" />',
                obj.image.url,
            )
        return "—"
    thumbnail_preview.short_description = "Preview"
