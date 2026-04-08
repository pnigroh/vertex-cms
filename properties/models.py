from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from treebeard.mp_tree import MP_Node


def property_image_upload_to(instance, filename):
    """Upload property images to media/listing/<property_id>/."""
    return f"listing/{instance.property_id}/{filename}"


# ---------------------------------------------------------------------------
# Location  (hierarchical via treebeard materialized-path)
# ---------------------------------------------------------------------------
class Location(MP_Node):
    """
    Hierarchical location tree.
    Example: USA > California > Los Angeles > Beverly Hills
    """

    LOCATION_TYPES = [
        ("country", _("Country")),
        ("state", _("State / Province")),
        ("city", _("City")),
        ("neighborhood", _("Neighborhood")),
    ]

    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), max_length=255)
    location_type = models.CharField(
        _("type"), max_length=20, choices=LOCATION_TYPES, default="city"
    )

    node_order_by = ["name"]

    class Meta:
        verbose_name = _("location")
        verbose_name_plural = _("locations")

    def __str__(self):
        """Return full ancestry path, e.g. 'USA > California > Los Angeles'."""
        ancestors = self.get_ancestors()
        parts = [a.name for a in ancestors] + [self.name]
        return " > ".join(parts)

    @property
    def short_name(self):
        return self.name


# ---------------------------------------------------------------------------
# Amenity category + Amenity
# ---------------------------------------------------------------------------
class AmenityCategory(models.Model):
    """Logical grouping for amenities (e.g. Interior, Exterior, Security)."""

    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), max_length=255, unique=True)
    order = models.PositiveIntegerField(_("order"), default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("amenity category")
        verbose_name_plural = _("amenity categories")

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Property status  (editable list)
# ---------------------------------------------------------------------------
class PropertyStatus(models.Model):
    """Editable status options for property listings."""

    name = models.CharField(_("name"), max_length=100, unique=True)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    order = models.PositiveIntegerField(_("order"), default=0)
    is_published_status = models.BooleanField(
        _("counts as published"),
        default=False,
        help_text=_("If checked, properties with this status appear on the public site."),
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("property status")
        verbose_name_plural = _("property statuses")

    def __str__(self):
        return self.name


class Amenity(models.Model):
    """Individual amenity item belonging to a category."""

    category = models.ForeignKey(
        AmenityCategory,
        on_delete=models.CASCADE,
        related_name="amenities",
        verbose_name=_("category"),
    )
    name = models.CharField(_("name"), max_length=255)
    icon = models.CharField(
        _("icon CSS class"),
        max_length=100,
        blank=True,
        help_text=_("Optional icon identifier, e.g. 'fa-swimming-pool'."),
    )
    order = models.PositiveIntegerField(_("order"), default=0)

    class Meta:
        ordering = ["category__order", "order", "name"]
        verbose_name = _("amenity")
        verbose_name_plural = _("amenities")

    def __str__(self):
        return f"{self.category.name} - {self.name}"


# ---------------------------------------------------------------------------
# Property  (translatable via django-parler)
# ---------------------------------------------------------------------------
class Property(TranslatableModel):
    """Core property listing with translated title/description/slug."""

    PROPERTY_TYPES = [
        ("house", _("House")),
        ("apartment", _("Apartment")),
        ("condo", _("Condo")),
        ("land", _("Land")),
        ("commercial", _("Commercial")),
        ("office", _("Office")),
    ]

    LISTING_TYPES = [
        ("sale", _("For Sale")),
        ("rent", _("For Rent")),
        ("sale_and_rent", _("For Sale & Rent")),
    ]

    CURRENCY_CHOICES = [
        ("USD", "USD"),
        ("EUR", "EUR"),
        ("GBP", "GBP"),
        ("MXN", "MXN"),
        ("CAD", "CAD"),
        ("COP", "COP"),
    ]

    # --- Translated fields ------------------------------------------------
    translations = TranslatedFields(
        title=models.CharField(_("title"), max_length=255),
        slug=models.SlugField(
            _("slug"),
            max_length=255,
            help_text=_("URL-friendly identifier (per language)."),
        ),
        description=models.TextField(_("description"), blank=True),
    )

    # --- Classification ----------------------------------------------------
    property_type = models.CharField(
        _("property type"), max_length=20, choices=PROPERTY_TYPES, default="house"
    )
    listing_type = models.CharField(
        _("listing type"), max_length=20, choices=LISTING_TYPES, default="sale"
    )

    # --- Specs -------------------------------------------------------------
    bedrooms = models.PositiveSmallIntegerField(
        _("bedrooms"), null=True, blank=True
    )
    bathrooms = models.DecimalField(
        _("bathrooms"), max_digits=3, decimal_places=1, null=True, blank=True
    )
    parking_spaces = models.PositiveSmallIntegerField(
        _("parking spaces"), default=0
    )
    construction_area = models.DecimalField(
        _("construction area (m\u00b2)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    lot_area = models.DecimalField(
        _("lot area (m\u00b2)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    year_built = models.PositiveSmallIntegerField(
        _("year built"), null=True, blank=True
    )

    # --- Pricing -----------------------------------------------------------
    sale_price = models.DecimalField(
        _("sale price"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    rental_price = models.DecimalField(
        _("rental price"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(
        _("currency"), max_length=3, choices=CURRENCY_CHOICES, default="USD"
    )

    # --- Relations ---------------------------------------------------------
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties",
        verbose_name=_("location"),
    )
    amenities = models.ManyToManyField(
        Amenity,
        blank=True,
        related_name="properties",
        verbose_name=_("amenities"),
    )

    # --- Status ------------------------------------------------------------
    status = models.ForeignKey(
        PropertyStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties",
        verbose_name=_("status"),
    )
    is_featured = models.BooleanField(_("featured"), default=False)

    # --- Timestamps --------------------------------------------------------
    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        verbose_name = _("property")
        verbose_name_plural = _("properties")
        ordering = ["-created_at"]

    def __str__(self):
        return self.safe_translation_getter("title", any_language=True) or f"Property #{self.pk}"

    @property
    def is_published(self):
        """Return True if the status is marked as a published status."""
        return self.status is not None and self.status.is_published_status

    @property
    def cover_image(self):
        """Return the cover PropertyImage, or the first image by order."""
        return (
            self.images.filter(is_cover=True).first()
            or self.images.first()
        )


# ---------------------------------------------------------------------------
# PropertyImage  (sortable via adminsortable2)
# ---------------------------------------------------------------------------
class PropertyImage(models.Model):
    """Image attached to a property, orderable via drag-and-drop."""

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("property"),
    )
    image = models.ImageField(
        _("image"),
        upload_to=property_image_upload_to,
    )
    alt_text = models.CharField(
        _("alt text"), max_length=255, blank=True
    )
    is_cover = models.BooleanField(_("cover image"), default=False)
    order = models.PositiveIntegerField(_("order"), default=0, db_index=True)

    class Meta:
        ordering = ["order"]
        verbose_name = _("property image")
        verbose_name_plural = _("property images")

    def __str__(self):
        return f"Image #{self.order} for {self.property}"
