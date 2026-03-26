"""
Runtime patches for djangocms-frontend plugins.

ENTANGLED FORMS — WHY WE BUILD NEW SUBCLASSES
----------------------------------------------
Django's CMSPluginBase.get_form() does this on every request:
    form = type(self.form.__name__, (self.form,), new_attrs)

EntangledFormMetaclass.__new__ asserts on every such call:
    assert field_name in new_class.base_fields

So every field in _meta.entangled_fields["config"] MUST be present in
base_fields at class-definition time.  We cannot mutate entangled_fields
after class creation — the assertion fires on the next request.

Solution: build a proper new form subclass at startup using type() so the
metaclass assertion runs once cleanly, then swap plugin.form.

FIELDSET INJECTION — THE MRO ORDERING PROBLEM
---------------------------------------------
BackgroundMixin.get_fieldsets calls super().get_fieldsets() and then appends
the "Background" block to whatever super() returned.  Our patch sits on
CMSUIPluginBase (the bottom of the chain) so when our code runs,
BackgroundMixin hasn't added its block yet.  We cannot append background_image
to a block that doesn't exist yet.

Solution: wrap BackgroundMixin.get_fieldsets directly so we can append
background_image after it builds its own block.  For every other plugin
(no BackgroundMixin) we inject a fresh "Background" block from our base patch.

BACKGROUND IMAGE RENDERING — HTML QUOTING
-----------------------------------------
The style attribute is delimited by double-quotes:
    style="background-image:url(...);"
So we must use single quotes inside url():
    url('/media/image.jpg')
BUT instance.add_attribute() passes the value through conditional_escape()
in get_attributes(), which turns ' into &#x27;, breaking the CSS.

Solution: we patch get_attributes() to NOT escape the value of "style"
(style values are author-controlled data, not user-controlled, so XSS is
not a concern here), and use single quotes inside url() which will NOT be
double-escaped.
"""

from __future__ import annotations
import django.forms as forms
from django.utils.translation import gettext_lazy as _
from entangled.forms import EntangledModelFormMixin


# ============================================================
# Form mixin classes — built at module level so their metaclass
# assertion runs cleanly before any plugin form is subclassed.
# ============================================================

class ExtraClassesMixin(EntangledModelFormMixin):
    class Meta:
        entangled_fields = {"config": ["extra_classes"]}

    extra_classes = forms.CharField(
        label=_("Extra CSS classes"),
        required=False,
        help_text=_(
            "Space-separated CSS class names added to the outermost element "
            "of this plugin (e.g. 'my-section text-white shadow-lg')."
        ),
        widget=forms.TextInput(attrs={"placeholder": "e.g. my-section hero-block"}),
    )


def _make_bg_image_field():
    try:
        from filer.fields.image import AdminImageFormField, FilerImageField
        from filer.models import Image as FilerImage
        from django.db.models.fields.related import ManyToOneRel
        return AdminImageFormField(
            rel=ManyToOneRel(FilerImageField, FilerImage, "id"),
            queryset=FilerImage.objects.all(),
            to_field_name="id",
            label=_("Background image"),
            required=False,
            help_text=_(
                "Image applied as CSS background on the outermost element. "
                "Combine with a semi-transparent colour for best results."
            ),
        )
    except Exception:
        return forms.URLField(label=_("Background image URL"), required=False)


BACKGROUND_SIZE_CHOICES = [
    ("", _("Default (cover)")),
    ("cover",   _("Cover — fill the element, crop if needed")),
    ("contain", _("Contain — fit inside the element, letterbox if needed")),
    ("auto",    _("Auto — use the image's natural size")),
    ("50%",     _("50%")),
    ("100% 100%", _("Stretch — fill exactly (may distort)")),
]

BACKGROUND_POSITION_CHOICES = [
    ("",              _("Default (center center)")),
    ("center center", _("Center")),
    ("top left",      _("Top left")),
    ("top center",    _("Top center")),
    ("top right",     _("Top right")),
    ("center left",   _("Center left")),
    ("center right",  _("Center right")),
    ("bottom left",   _("Bottom left")),
    ("bottom center", _("Bottom center")),
    ("bottom right",  _("Bottom right")),
]


from djangocms_frontend.common.bootstrap5.background import BackgroundFormMixin as _UpstreamBackgroundFormMixin  # noqa: E402


class BackgroundImageMixin(_UpstreamBackgroundFormMixin):
    """
    Full background mixin for plugins that do NOT already have BackgroundMixin.
    Inherits background_context / background_opacity / background_shadow from
    upstream BackgroundFormMixin, then adds background_image, background_size,
    and background_position on top.
    """
    class Meta:
        # entangled merges parent Meta automatically, so we only declare the
        # new fields here — the three colour fields come from the parent.
        entangled_fields = {"config": [
            "background_image",
            "background_size",
            "background_position",
        ]}

    background_image = _make_bg_image_field()

    background_size = forms.ChoiceField(
        label=_("Background size"),
        choices=BACKGROUND_SIZE_CHOICES,
        required=False,
        initial="",
        help_text=_("How the background image is scaled inside the element."),
    )

    background_position = forms.ChoiceField(
        label=_("Background position"),
        choices=BACKGROUND_POSITION_CHOICES,
        required=False,
        initial="",
        help_text=_("Where the background image is anchored inside the element."),
    )


# ============================================================
# Patch 1 — Extend GridRowPlugin with full Background support
# ============================================================

def _patch_grid_row():
    from djangocms_frontend.common import BackgroundMixin
    from djangocms_frontend.common.bootstrap5.background import BackgroundFormMixin
    from djangocms_frontend.contrib.grid.cms_plugins import GridRowPlugin
    from djangocms_frontend.contrib.grid.forms import GridRowForm

    if BackgroundMixin not in GridRowPlugin.__mro__:
        GridRowPlugin.__bases__ = (BackgroundMixin,) + GridRowPlugin.__bases__

    bg_fields = ["background_context", "background_opacity", "background_shadow"]
    if any(f not in GridRowForm._meta.entangled_fields.get("config", []) for f in bg_fields):
        new_form = type(
            GridRowForm.__name__,
            (BackgroundFormMixin, GridRowForm),
            {"__module__": GridRowForm.__module__},
        )
        GridRowPlugin.form = new_form


# ============================================================
# Patch 2 — Extend every plugin's form with extra_classes +
#            background_image via proper entangled subclassing
# ============================================================

def _extend_plugin_forms():
    from cms.plugin_pool import plugin_pool
    plugin_pool.get_all_plugins()

    for plugin_cls in list(plugin_pool.plugins.values()):
        if not plugin_cls.__module__.startswith("djangocms_frontend"):
            continue
        form_cls = getattr(plugin_cls, "form", None)
        if form_cls is None:
            continue
        meta = getattr(form_cls, "_meta", None)
        if meta is None or "config" not in getattr(meta, "entangled_fields", {}):
            continue

        needs_extra = "extra_classes"    not in meta.entangled_fields["config"]
        needs_bg    = "background_image" not in meta.entangled_fields["config"]
        if not needs_extra and not needs_bg:
            continue

        bases = []
        if needs_extra:
            bases.append(ExtraClassesMixin)
        if needs_bg:
            bases.append(BackgroundImageMixin)

        plugin_cls.form = type(
            form_cls.__name__,
            tuple(bases) + (form_cls,),
            {"__module__": form_cls.__module__},
        )


# ============================================================
# Patch 3 — Render: apply extra_classes and background_image
#            on every plugin before the template renders.
#
# We patch CMSUIPluginBase.render at the very bottom of the
# MRO so it fires for every plugin exactly once.
# ============================================================

def _apply_bg_image(instance):
    """
    Read background_image from instance.config, resolve the filer image,
    and inject a background-image inline style.

    Uses single quotes inside url() because get_attributes() wraps the
    whole attribute value in double-quotes.  The style value is stored
    as plain text; our patched get_attributes() will mark it safe so
    conditional_escape() does not re-escape the single quotes.
    """
    cfg = getattr(instance, "config", None) or {}
    if not cfg.get("background_image"):
        return
    try:
        from djangocms_frontend.helpers import get_related_object
        img = get_related_object(cfg, "background_image")
        if not img:
            return
        url = img.url
        if not url:
            return
        # Read editor-chosen size/position, fall back to sensible defaults.
        size     = (cfg.get("background_size")     or "cover").strip()
        position = (cfg.get("background_position") or "center center").strip()

        # Single quotes inside url() — safe because get_attributes() marks
        # the style value as safe (see Patch 5 below).
        new_style = (
            f"background-image:url('{url}');"
            f"background-size:{size};"
            f"background-position:{position};"
        )
        # Prepend any existing inline style already in config
        existing = cfg.get("attributes", {}).get("style", "")
        if existing:
            new_style = existing.rstrip(";") + ";" + new_style
        instance.add_attribute("style", new_style)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("_apply_bg_image failed: %s", exc)


def _patch_render():
    from djangocms_frontend.ui_plugin_base import CMSUIPluginBase

    _orig = CMSUIPluginBase.render

    def render(self, context, instance, placeholder):
        from djangocms_frontend.common import BackgroundMixin

        # Apply extra CSS classes from the free-text field
        extra = (getattr(instance, "extra_classes", "") or "").strip()
        if extra:
            instance.add_classes(extra)

        # For plugins WITHOUT BackgroundMixin, apply the colour/opacity/shadow
        # classes ourselves (BackgroundMixin.render handles its own plugins).
        if not isinstance(self, BackgroundMixin):
            ctx = (getattr(instance, "background_context", "") or "").strip()
            if ctx:
                instance.add_classes(f"bg-{ctx}")
            opacity = (getattr(instance, "background_opacity", "") or "").strip()
            if opacity:
                instance.add_classes(f"bg-opacity-{opacity}")
            shadow = (getattr(instance, "background_shadow", "") or "").strip()
            if shadow:
                instance.add_classes("shadow" if shadow == "reg" else f"shadow-{shadow}")

        # Apply background image inline style (all plugins)
        _apply_bg_image(instance)
        return _orig(self, context, instance, placeholder)

    CMSUIPluginBase.render = render


# ============================================================
# Patch 4 — Fieldsets: inject extra_classes and background_image
#            into every plugin's edit form.
#
# STRATEGY:
#   • extra_classes  → always injected by our CMSUIPluginBase patch
#                      (runs after the whole super() chain, so it sees
#                       the fully-assembled fieldset list)
#   • background_image for plugins WITH BackgroundMixin (GridRow,
#     GridColumn, GridContainer, Card …):
#       We wrap BackgroundMixin.get_fieldsets so we can append
#       background_image to the block it just built.
#   • background_image for plugins WITHOUT BackgroundMixin:
#       Injected as a new "Background" block by our CMSUIPluginBase patch.
# ============================================================

def _patch_background_mixin_fieldsets():
    """
    Wrap BackgroundMixin.get_fieldsets to append background_image to the
    'Background' block it produces.
    """
    from djangocms_frontend.common.bootstrap5.background import BackgroundMixin

    _orig = BackgroundMixin.get_fieldsets

    def get_fieldsets(self, request, obj=None):
        # Let BackgroundMixin build its block first
        fieldsets = _orig(self, request, obj)

        # Only proceed if the form actually carries background_image
        form_cls = getattr(self, "form", None)
        if form_cls is None:
            return fieldsets
        if "background_image" not in getattr(form_cls, "base_fields", {}):
            return fieldsets

        # Append background image fields to the "Background" block
        new_bg_rows = [
            f for f in ("background_image", "background_size", "background_position")
            if f in getattr(form_cls, "base_fields", {})
        ]

        result = []
        for name, opts in fieldsets:
            if str(name) == str(_("Background")) or name == "Background":
                new_opts = dict(opts)
                fields = list(new_opts.get("fields", ()))
                flat = [f for row in fields
                        for f in (list(row) if isinstance(row, (list, tuple)) else [row])]
                for f in new_bg_rows:
                    if f not in flat:
                        fields.append(f)
                new_opts["fields"] = tuple(fields)
                result.append((name, new_opts))
            else:
                result.append((name, opts))

        return result

    BackgroundMixin.get_fieldsets = get_fieldsets


def _patch_base_fieldsets():
    """
    Wrap CMSUIPluginBase.get_fieldsets to:
     1. Append extra_classes fieldset (every plugin).
     2. Inject a 'Background' fieldset with background_image for plugins
        that do NOT have BackgroundMixin (those are handled above).
    """
    from djangocms_frontend.ui_plugin_base import CMSUIPluginBase
    from djangocms_frontend.common.bootstrap5.background import BackgroundMixin
    from djangocms_frontend.helpers import insert_fields

    _orig = CMSUIPluginBase.get_fieldsets

    def get_fieldsets(self, request, obj=None):
        fieldsets = _orig(self, request, obj)
        form_cls  = getattr(self, "form", None)
        if form_cls is None:
            return fieldsets
        base_fields = getattr(form_cls, "base_fields", {})

        def already_present(name):
            for _, opts in fieldsets:
                for row in opts.get("fields", ()):
                    items = list(row) if isinstance(row, (list, tuple)) else [row]
                    if name in items:
                        return True
            return False

        # 1. extra_classes — always, for every plugin
        if "extra_classes" in base_fields and not already_present("extra_classes"):
            fieldsets = insert_fields(
                fieldsets,
                ("extra_classes",),
                blockname=_("Extra CSS classes"),
                blockattrs={"description": _(
                    "Space-separated CSS class names added to the outermost "
                    "HTML element of this plugin."
                )},
                position=-1,
            )

        # 2. Full background block — only for plugins WITHOUT BackgroundMixin
        #    (BackgroundMixin plugins already get colour from upstream and
        #    image/size/position via _patch_background_mixin_fieldsets).
        if (
            "background_image" in base_fields
            and not already_present("background_image")
            and not isinstance(self, BackgroundMixin)
        ):
            # Row 1: colour context (coloured button-group widget)
            # Row 2: opacity + shadow side-by-side
            # Row 3: image picker
            # Row 4: size + position side-by-side
            bg_rows = []
            if "background_context" in base_fields:
                bg_rows.append("background_context")
            if "background_opacity" in base_fields and "background_shadow" in base_fields:
                bg_rows.append(("background_opacity", "background_shadow"))
            elif "background_opacity" in base_fields:
                bg_rows.append("background_opacity")
            elif "background_shadow" in base_fields:
                bg_rows.append("background_shadow")
            if "background_image" in base_fields:
                bg_rows.append("background_image")
            size_pos = tuple(
                f for f in ("background_size", "background_position")
                if f in base_fields
            )
            if size_pos:
                bg_rows.append(size_pos)
            fieldsets = insert_fields(
                fieldsets,
                tuple(bg_rows),
                blockname=_("Background"),
                blockattrs={"description": _(
                    "Background colour, image, size and position applied to "
                    "the outermost element of this plugin."
                )},
                position=-1,
            )

        return fieldsets

    CMSUIPluginBase.get_fieldsets = get_fieldsets


# ============================================================
# Patch 5 — Fix get_attributes() to:
#   a) Not HTML-escape the value of "style" (so url('/…') stays intact)
#   b) Always put a space between class="…" and any following attribute
# ============================================================

def _patch_get_attributes():
    from djangocms_frontend.models import AbstractFrontendUIItem
    from django.utils.html import conditional_escape, mark_safe

    def get_attributes(self):
        attributes = self.config.get("attributes", {})
        classes = self.get_classes()
        parts = []
        if classes:
            parts.append(f'class="{classes}"')
        for attr, value in attributes.items():
            if attr == "class":
                continue  # already handled above
            if attr == "style" and value:
                # Do NOT escape the style value — it is author-controlled and
                # must preserve url('…') single quotes intact.
                parts.append(f'style="{value}"')
            elif value:
                parts.append(f'{attr}="{conditional_escape(value)}"')
            else:
                parts.append(attr)
        result = " ".join(parts)
        return mark_safe(" " + result) if result else ""

    AbstractFrontendUIItem.get_attributes = get_attributes


# ============================================================
# Run all patches — ORDER MATTERS
# ============================================================

# 1. Extend GridRowPlugin before _extend_plugin_forms so the form
#    replacement sees the already-extended base.
_patch_grid_row()

# 2. Extend every plugin's form with extra_classes + background_image.
#    Must run before fieldset patches (which read self.form.base_fields).
_extend_plugin_forms()

# 3. Render patch — single hook at the base, fires for every plugin.
_patch_render()

# 4a. Fieldset patch for BackgroundMixin plugins (GridRow, Column, Card…)
#     Must run BEFORE the base fieldset patch so the Background block
#     already contains background_image when the base patch checks.
_patch_background_mixin_fieldsets()

# 4b. Fieldset patch at the base — extra_classes + background_image
#     for non-BackgroundMixin plugins.
_patch_base_fieldsets()

# 5. Fix get_attributes() HTML quoting.
_patch_get_attributes()
