# Decisions Log — Vertex CMS

> Append-only journal. New entries go at the bottom. Never edit or delete existing entries.

---

## DEC-001: Use django-jazzmin as admin theme

- **Date**: 2026-04-08
- **Commit**: `a7d1930`
- **Context**: The default Django admin is functional but visually plain. The project needed a modern admin UI with sidebar navigation, icons, and branding for the Vertex CMS identity.
- **Decision**: Added `django-jazzmin>=3.0` to requirements and configured `JAZZMIN_SETTINGS` / `JAZZMIN_UI_TWEAKS` in settings.py with Vertex CMS branding, model icons, and horizontal_tabs changeform format.
- **Alternatives considered**: Django Unfold (mentioned in LAPCS project context, but Jazzmin was chosen here). Django Grappelli. Default admin.
- **Consequences**: Jazzmin must be listed before `django.contrib.admin` in INSTALLED_APPS. Some admin templates may need Jazzmin-specific overrides.

---

## DEC-002: django-parler for Property model translations

- **Date**: 2026-04-08
- **Commit**: `a7d1930`
- **Context**: Properties need multilingual title, slug, and description fields. django-cms handles page-level i18n but Property is a standalone model.
- **Decision**: Use `django-parler` with `TranslatableModel` / `TranslatedFields` for the Property model. Configured `PARLER_LANGUAGES` for en/es/fr with English fallback.
- **Consequences**: All Property queries that access translated fields must use `.translated(lang)` or `.active_translations()`. Admin uses `TranslatableAdmin` from parler.

---

## DEC-003: treebeard MP_Node for Location hierarchy

- **Date**: 2026-04-08
- **Commit**: `a7d1930`
- **Context**: Locations need a tree structure (Country > State > City > Neighborhood). django-cms already depends on treebeard.
- **Decision**: Use `treebeard.mp_tree.MP_Node` for the Location model. Admin uses `TreeAdmin` with `movenodeform_factory`.
- **Consequences**: treebeard is already a dependency (via django-cms). Materialized-path gives fast reads but tree mutations require careful handling.

---

## DEC-004: PropertyStatus as editable model rather than CharField choices

- **Date**: 2026-04-08
- **Commit**: `a7d1930`
- **Context**: Property statuses (Active, Sold, Pending, etc.) should be editable by the client without code changes.
- **Decision**: Created `PropertyStatus` model with `is_published_status` boolean flag. Property.status is a ForeignKey. The `@property is_published` checks `status.is_published_status`.
- **Consequences**: Flexible but adds a join. Public views must filter on `status__is_published_status=True` (not the Python property).

---

## DEC-005: Monkey-patch djangocms-frontend plugins for extra CSS + backgrounds

- **Date**: 2026-03-26
- **Commit**: `04ca2f9`
- **Context**: Every djangocms-frontend plugin needed extra_classes and background_image fields. Forking the entire library was impractical.
- **Decision**: Created `frontend_extensions` app that patches all plugin forms, renderers, and fieldsets at startup via `AppConfig.ready()`. Uses proper entangled form subclassing to satisfy metaclass assertions.
- **Consequences**: Fragile coupling to djangocms-frontend internals. Upgrades to djangocms-frontend may break patches. The patches file is heavily commented to explain each workaround.

---

## DEC-006: Plain ImageField for PropertyImage (not django-filer)

- **Date**: 2026-04-08
- **Commit**: `a7d1930`
- **Context**: Property images are listing-specific photos, not reusable assets. django-filer adds complexity for images that are only used in one context.
- **Decision**: Use plain `models.ImageField` with `upload_to=listing/<property_id>/` for property images. Service model keeps `FilerImageField` since services images may be reused.
- **Consequences**: Two image management patterns in the same project. Property images are not browsable in the filer library.

---

## DEC-007: Bulk image upload via custom admin view

- **Date**: 2026-04-08
- **Commit**: `a7d1930`
- **Context**: Adding property images one-by-one through inline admin is tedious for real estate listings that may have 20+ photos.
- **Decision**: Added custom admin URL `<property_id>/upload-images/` with popup template. JavaScript handles multi-file selection, AJAX upload, progress display. Server validates content type and enforces 10MB limit.
- **Consequences**: Custom JavaScript (`bulk_upload.js`) and popup template. The popup is launched from the change form via a button injected by the custom `change_form.html` template.
