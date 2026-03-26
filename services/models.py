from django.db import models
from django.utils.translation import gettext_lazy as _
from filer.fields.image import FilerImageField


class Service(models.Model):
    """
    A Service entry with an intro text, HTML content body, and an image.
    """

    title = models.CharField(
        _("Title"),
        max_length=255,
        help_text=_("The name / headline of this service."),
    )

    slug = models.SlugField(
        _("Slug"),
        max_length=255,
        unique=True,
        help_text=_("URL-friendly identifier, auto-generated from the title."),
    )

    intro = models.TextField(
        _("Intro text"),
        help_text=_("A short introductory paragraph shown in listings and teasers."),
    )

    content = models.TextField(
        _("Content"),
        help_text=_("Full HTML content for this service. Use the rich-text editor."),
        blank=True,
    )

    image = FilerImageField(
        verbose_name=_("Image"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_image",
        help_text=_("Main visual for this service."),
    )

    is_published = models.BooleanField(
        _("Published"),
        default=True,
        help_text=_("Uncheck to hide this service from the public site."),
    )

    created_at = models.DateTimeField(_("Created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ["title"]

    def __str__(self):
        return self.title
