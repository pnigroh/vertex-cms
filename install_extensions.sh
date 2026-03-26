#!/usr/bin/env bash
# =============================================================================
# install_extensions.sh
#
# Applies the frontend_extensions customisations to a fresh Django CMS /
# djangocms-frontend installation.
#
# WHAT IT DOES
# ------------
# 1. Creates the frontend_extensions Django app (Extra CSS classes +
#    full Background controls on every plugin).
# 2. Patches mysite/settings.py to activate the app and theme.
#
# PREREQUISITES
# -------------
# • A working Django CMS project with djangocms-frontend installed.
# • django-filer installed (for the background image picker).
# • The script must be run from the Django project root
#   (the directory that contains manage.py).
# • Python/Django environment must already be active.
#
# USAGE
# -----
#   cd /path/to/your/django/project
#   bash install_extensions.sh
#
# Then add "frontend_extensions" to INSTALLED_APPS and set
# DJANGOCMS_FRONTEND_THEME = "frontend_extensions" in your settings
# (the script will tell you exactly what to add).
# =============================================================================

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

info()    { echo -e "${CYAN}[info]${RESET} $*"; }
success() { echo -e "${GREEN}[ok]${RESET}   $*"; }
warn()    { echo -e "${YELLOW}[warn]${RESET} $*"; }

# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------

if [ ! -f manage.py ]; then
    echo "ERROR: manage.py not found. Run this script from your Django project root."
    exit 1
fi

if [ -d frontend_extensions ]; then
    warn "frontend_extensions/ already exists — skipping creation."
    warn "Delete it first if you want a clean install."
    exit 0
fi

info "Creating frontend_extensions app..."

# ---------------------------------------------------------------------------
# Directory structure
# ---------------------------------------------------------------------------

mkdir -p frontend_extensions/frameworks

# ---------------------------------------------------------------------------
# frontend_extensions/__init__.py
# ---------------------------------------------------------------------------

cat > frontend_extensions/__init__.py << 'PYEOF'
PYEOF
success "frontend_extensions/__init__.py"

# ---------------------------------------------------------------------------
# frontend_extensions/frameworks/__init__.py
# ---------------------------------------------------------------------------

cat > frontend_extensions/frameworks/__init__.py << 'PYEOF'
PYEOF
success "frontend_extensions/frameworks/__init__.py"

# ---------------------------------------------------------------------------
# frontend_extensions/apps.py
# ---------------------------------------------------------------------------

cat > frontend_extensions/apps.py << 'PYEOF'
from django.apps import AppConfig


class FrontendExtensionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "frontend_extensions"
    verbose_name = "Frontend Extensions"

    def ready(self):
        from . import patches  # noqa: F401
PYEOF
success "frontend_extensions/apps.py"

# ---------------------------------------------------------------------------
# frontend_extensions/forms.py  (stub — theme compatibility)
# ---------------------------------------------------------------------------

cat > frontend_extensions/forms.py << 'PYEOF'
"""
Theme form stub.

djangocms-frontend imports this module as `{DJANGOCMS_FRONTEND_THEME}.forms`.
The actual form extensions are in patches.py.
"""
PYEOF
success "frontend_extensions/forms.py"

# ---------------------------------------------------------------------------
# frontend_extensions/frameworks/bootstrap5.py
# ---------------------------------------------------------------------------

cat > frontend_extensions/frameworks/bootstrap5.py << 'PYEOF'
"""
Theme render mixin stubs for djangocms-frontend (Bootstrap 5).

djangocms-frontend's mixin_factory() looks for {Name}RenderMixin classes here
and mixes them into plugin renderers at import time for plugins that use
mixin_factory(). The base render patch in patches.py covers all plugins
uniformly; these stubs are a belt-and-braces safety net.
"""

from djangocms_frontend.common.bootstrap5.background import BackgroundMixin


class _ExtraClassesRenderMixin:
    def render(self, context, instance, placeholder):
        extra = getattr(instance, "extra_classes", "") or ""
        if extra.strip():
            instance.add_classes(extra.strip())
        return super().render(context, instance, placeholder)


# One stub per plugin name.  Add new {Name}RenderMixin classes here if you
# need plugin-specific render behaviour beyond extra_classes.

class AccordionRenderMixin(_ExtraClassesRenderMixin): pass
class AccordionItemRenderMixin(_ExtraClassesRenderMixin): pass
class AlertRenderMixin(_ExtraClassesRenderMixin): pass
class BadgeRenderMixin(_ExtraClassesRenderMixin): pass
class BlockquoteRenderMixin(_ExtraClassesRenderMixin): pass
class CardRenderMixin(_ExtraClassesRenderMixin): pass
class CardLayoutRenderMixin(_ExtraClassesRenderMixin): pass
class CarouselRenderMixin(_ExtraClassesRenderMixin): pass
class CarouselSlideRenderMixin(_ExtraClassesRenderMixin): pass
class CodeRenderMixin(_ExtraClassesRenderMixin): pass
class CollapseRenderMixin(_ExtraClassesRenderMixin): pass
class CollapseTriggerRenderMixin(_ExtraClassesRenderMixin): pass
class CollapseContainerRenderMixin(_ExtraClassesRenderMixin): pass
class FigureRenderMixin(_ExtraClassesRenderMixin): pass
class GridContainerRenderMixin(_ExtraClassesRenderMixin): pass
class GridRowRenderMixin(BackgroundMixin, _ExtraClassesRenderMixin): pass
class GridColumnRenderMixin(_ExtraClassesRenderMixin): pass
class HeadingRenderMixin(_ExtraClassesRenderMixin): pass
class IconRenderMixin(_ExtraClassesRenderMixin): pass
class ImageRenderMixin(_ExtraClassesRenderMixin): pass
class JumbotronRenderMixin(_ExtraClassesRenderMixin): pass
class LinkRenderMixin(_ExtraClassesRenderMixin): pass
class ListGroupRenderMixin(_ExtraClassesRenderMixin): pass
class ListGroupItemRenderMixin(_ExtraClassesRenderMixin): pass
class MediaRenderMixin(_ExtraClassesRenderMixin): pass
class MediaBodyRenderMixin(_ExtraClassesRenderMixin): pass
class NavBrandRenderMixin(_ExtraClassesRenderMixin): pass
class NavLinkRenderMixin(_ExtraClassesRenderMixin): pass
class NavigationRenderMixin(_ExtraClassesRenderMixin): pass
class PageTreeRenderMixin(_ExtraClassesRenderMixin): pass
class SpacingRenderMixin(_ExtraClassesRenderMixin): pass
class TabRenderMixin(_ExtraClassesRenderMixin): pass
class TabItemRenderMixin(_ExtraClassesRenderMixin): pass
class TOCRenderMixin(_ExtraClassesRenderMixin): pass
class TableOfContentsRenderMixin(_ExtraClassesRenderMixin): pass
PYEOF
success "frontend_extensions/frameworks/bootstrap5.py"

# ---------------------------------------------------------------------------
# frontend_extensions/patches.py  — the core of all customisations
# ---------------------------------------------------------------------------

cat > frontend_extensions/patches.py << 'PYEOF'
"""
Runtime patches for djangocms-frontend plugins.

Activated by frontend_extensions/apps.py FrontendExtensionsConfig.ready().

Adds to every djangocms-frontend plugin:
  • Extra CSS classes    — free-text field, applied to the outermost element
  • Background colour    — Bootstrap bg-* context + opacity + shadow
  • Background image     — filer image picker, rendered as inline CSS style
  • Background size      — CSS background-size choices
  • Background position  — CSS background-position choices

Also:
  • Adds background colour/image support to GridRowPlugin (missing upstream)
  • Fixes get_attributes() HTML quoting (style value escaping + spacing)

CUSTOMISATION GUIDE
-------------------
• To change background-size choices:    edit BACKGROUND_SIZE_CHOICES
• To change background-position choices: edit BACKGROUND_POSITION_CHOICES
• To change field labels or help text:   edit ExtraClassesMixin /
                                         BackgroundImageMixin field definitions
• To change fallback size/position:      edit _apply_bg_image()
"""

from __future__ import annotations
import django.forms as forms
from django.utils.translation import gettext_lazy as _
from entangled.forms import EntangledModelFormMixin


# ============================================================
# Choices — edit these to add/remove options in the edit form
# ============================================================

BACKGROUND_SIZE_CHOICES = [
    ("",            _("Default (cover)")),
    ("cover",       _("Cover — fill the element, crop if needed")),
    ("contain",     _("Contain — fit inside the element, letterbox if needed")),
    ("auto",        _("Auto — use the image's natural size")),
    ("50%",         _("50%")),
    ("100% 100%",   _("Stretch — fill exactly (may distort)")),
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


# ============================================================
# Form mixin classes
# ============================================================

class ExtraClassesMixin(EntangledModelFormMixin):
    """Adds the 'Extra CSS classes' text input to any plugin form."""
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


from djangocms_frontend.common.bootstrap5.background import BackgroundFormMixin as _UpstreamBGFormMixin  # noqa: E402


class BackgroundImageMixin(_UpstreamBGFormMixin):
    """
    Full background form mixin for plugins without upstream BackgroundMixin.
    Inherits background_context / background_opacity / background_shadow from
    upstream, and adds background_image, background_size, background_position.
    """
    class Meta:
        entangled_fields = {"config": [
            "background_image",
            "background_size",
            "background_position",
        ]}

    background_image    = _make_bg_image_field()

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
# Patch 1 — GridRowPlugin: add full Background support
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
        GridRowPlugin.form = type(
            GridRowForm.__name__,
            (BackgroundFormMixin, GridRowForm),
            {"__module__": GridRowForm.__module__},
        )


# ============================================================
# Patch 2 — Replace every plugin's form with an extended subclass
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
# Patch 3 — Render: apply all background options + extra_classes
# ============================================================

def _apply_bg_image(instance):
    """Inject background-image inline style from saved config."""
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
        size     = (cfg.get("background_size")     or "cover").strip()
        position = (cfg.get("background_position") or "center center").strip()
        new_style = (
            f"background-image:url('{url}');"
            f"background-size:{size};"
            f"background-position:{position};"
        )
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

        # Extra CSS classes
        extra = (getattr(instance, "extra_classes", "") or "").strip()
        if extra:
            instance.add_classes(extra)

        # Background colour/opacity/shadow for plugins without BackgroundMixin
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

        # Background image
        _apply_bg_image(instance)
        return _orig(self, context, instance, placeholder)

    CMSUIPluginBase.render = render


# ============================================================
# Patch 4a — BackgroundMixin plugins: append image/size/position
#             to their existing Background fieldset block
# ============================================================

def _patch_background_mixin_fieldsets():
    from djangocms_frontend.common.bootstrap5.background import BackgroundMixin

    _orig = BackgroundMixin.get_fieldsets

    def get_fieldsets(self, request, obj=None):
        fieldsets = _orig(self, request, obj)
        form_cls = getattr(self, "form", None)
        if form_cls is None or "background_image" not in getattr(form_cls, "base_fields", {}):
            return fieldsets

        new_rows = [
            f for f in ("background_image", "background_size", "background_position")
            if f in getattr(form_cls, "base_fields", {})
        ]

        result = []
        for name, opts in fieldsets:
            if str(name) in (str(_("Background")), "Background"):
                new_opts = dict(opts)
                fields = list(new_opts.get("fields", ()))
                flat = [f for row in fields
                        for f in (list(row) if isinstance(row, (list, tuple)) else [row])]
                for f in new_rows:
                    if f not in flat:
                        fields.append(f)
                new_opts["fields"] = tuple(fields)
                result.append((name, new_opts))
            else:
                result.append((name, opts))
        return result

    BackgroundMixin.get_fieldsets = get_fieldsets


# ============================================================
# Patch 4b — Base fieldsets: extra_classes + full Background block
#             for plugins without BackgroundMixin
# ============================================================

def _patch_base_fieldsets():
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

        # Extra CSS classes — every plugin
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

        # Full Background block — only for non-BackgroundMixin plugins
        if (
            "background_image" in base_fields
            and not already_present("background_image")
            and not isinstance(self, BackgroundMixin)
        ):
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
# Patch 5 — Fix get_attributes() HTML quoting
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
                continue
            if attr == "style" and value:
                # Do not escape style values — must preserve url('…') quotes.
                parts.append(f'style="{value}"')
            elif value:
                parts.append(f'{attr}="{conditional_escape(value)}"')
            else:
                parts.append(attr)
        result = " ".join(parts)
        return mark_safe(" " + result) if result else ""

    AbstractFrontendUIItem.get_attributes = get_attributes


# ============================================================
# Run all patches — order matters
# ============================================================

_patch_grid_row()                    # 1. GridRow gets BackgroundMixin
_extend_plugin_forms()               # 2. All plugin forms extended
_patch_render()                      # 3. Render hook
_patch_background_mixin_fieldsets()  # 4a. BackgroundMixin plugin fieldsets
_patch_base_fieldsets()              # 4b. All other plugin fieldsets
_patch_get_attributes()              # 5. HTML attribute quoting fix
PYEOF
success "frontend_extensions/patches.py"

# ---------------------------------------------------------------------------
# Print manual steps
# ---------------------------------------------------------------------------

echo ""
echo -e "${BOLD}============================================================${RESET}"
echo -e "${BOLD} Installation complete — two manual steps required          ${RESET}"
echo -e "${BOLD}============================================================${RESET}"
echo ""
echo -e "${BOLD}Step 1${RESET} — Add to INSTALLED_APPS in your settings.py:"
echo ""
echo '    INSTALLED_APPS = ['
echo '        ...'
echo '        "djangocms_frontend",                    # must already be here'
echo '        "djangocms_frontend.contrib.grid",       # must already be here'
echo '        # ... other djangocms_frontend.contrib.* apps ...'
echo '        "frontend_extensions",                   # ← ADD THIS (after all frontend apps)'
echo '    ]'
echo ""
echo -e "${BOLD}Step 2${RESET} — Add to the bottom of settings.py:"
echo ""
echo '    DJANGOCMS_FRONTEND_THEME = "frontend_extensions"'
echo ""
echo -e "${BOLD}Step 3${RESET} — Restart your Django server."
echo ""
echo -e "${GREEN}No migrations are required — all data is stored in existing${RESET}"
echo -e "${GREEN}plugin JSON config fields.${RESET}"
echo ""
