"""
Theme render mixins for djangocms-frontend (Bootstrap 5 framework).

Loaded as `{DJANGOCMS_FRONTEND_THEME}.frameworks.bootstrap5`.
djangocms-frontend merges `{Name}RenderMixin` into the plugin's renderer
for plugins built via mixin_factory.

Every mixin here applies `extra_classes` to the outermost element.
GridRow additionally inherits BackgroundMixin so it gets bg-* colour classes.
Background image rendering for ALL plugins is handled centrally in
patches.py by patching BackgroundMixin.render — no duplication needed here.
"""

from djangocms_frontend.common.bootstrap5.background import BackgroundMixin


class _ExtraClassesRenderMixin:
    """Applies extra_classes config value to the plugin's root element."""

    def render(self, context, instance, placeholder):
        extra = getattr(instance, "extra_classes", "") or ""
        if extra.strip():
            instance.add_classes(extra.strip())
        return super().render(context, instance, placeholder)


# ---------------------------------------------------------------------------
# Per-plugin render mixins
# All get extra_classes. GridRow also gets BackgroundMixin (colour/opacity/
# shadow/image).
# ---------------------------------------------------------------------------

class AccordionRenderMixin(_ExtraClassesRenderMixin):
    pass

class AccordionItemRenderMixin(_ExtraClassesRenderMixin):
    pass

class AlertRenderMixin(_ExtraClassesRenderMixin):
    pass

class BadgeRenderMixin(_ExtraClassesRenderMixin):
    pass

class BlockquoteRenderMixin(_ExtraClassesRenderMixin):
    pass

class CardRenderMixin(_ExtraClassesRenderMixin):
    pass

class CardLayoutRenderMixin(_ExtraClassesRenderMixin):
    pass

class CarouselRenderMixin(_ExtraClassesRenderMixin):
    pass

class CarouselSlideRenderMixin(_ExtraClassesRenderMixin):
    pass

class CodeRenderMixin(_ExtraClassesRenderMixin):
    pass

class CollapseRenderMixin(_ExtraClassesRenderMixin):
    pass

class CollapseTriggerRenderMixin(_ExtraClassesRenderMixin):
    pass

class CollapseContainerRenderMixin(_ExtraClassesRenderMixin):
    pass

class FigureRenderMixin(_ExtraClassesRenderMixin):
    pass

class GridContainerRenderMixin(_ExtraClassesRenderMixin):
    pass

# GridRow: BackgroundMixin adds bg-* colour classes via its render() method,
# then calls super() which chains into _ExtraClassesRenderMixin.
class GridRowRenderMixin(BackgroundMixin, _ExtraClassesRenderMixin):
    pass

class GridColumnRenderMixin(_ExtraClassesRenderMixin):
    pass

class HeadingRenderMixin(_ExtraClassesRenderMixin):
    pass

class IconRenderMixin(_ExtraClassesRenderMixin):
    pass

class ImageRenderMixin(_ExtraClassesRenderMixin):
    pass

class JumbotronRenderMixin(_ExtraClassesRenderMixin):
    pass

class LinkRenderMixin(_ExtraClassesRenderMixin):
    pass

class ListGroupRenderMixin(_ExtraClassesRenderMixin):
    pass

class ListGroupItemRenderMixin(_ExtraClassesRenderMixin):
    pass

class MediaRenderMixin(_ExtraClassesRenderMixin):
    pass

class MediaBodyRenderMixin(_ExtraClassesRenderMixin):
    pass

class NavBrandRenderMixin(_ExtraClassesRenderMixin):
    pass

class NavLinkRenderMixin(_ExtraClassesRenderMixin):
    pass

class NavigationRenderMixin(_ExtraClassesRenderMixin):
    pass

class PageTreeRenderMixin(_ExtraClassesRenderMixin):
    pass

class SpacingRenderMixin(_ExtraClassesRenderMixin):
    pass

class TabRenderMixin(_ExtraClassesRenderMixin):
    pass

class TabItemRenderMixin(_ExtraClassesRenderMixin):
    pass

class TOCRenderMixin(_ExtraClassesRenderMixin):
    pass

class TableOfContentsRenderMixin(_ExtraClassesRenderMixin):
    pass
