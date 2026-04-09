# LLM Handoff — Vertex CMS

> Read this first when starting a new session. Then read `active-context.md` for current state.

## What This Project Is

Vertex CMS is a Django-based real-estate content management system. It combines:
- **django-cms v4** for page-level content (home, standard pages, services pages)
- **A `properties` app** for real-estate listings with translations, images, locations, amenities
- **A `services` app** for business services content
- **`frontend_extensions`** that monkey-patch all djangocms-frontend plugins to add extra CSS classes and background image support

It runs in Docker Compose with PostgreSQL 15.

## Current State (as of 2026-04-08)

- **Working**: CMS scaffolding, services app, properties models + admin, Jazzmin admin theme, frontend extensions, Docker setup
- **Not working**: Property public views have a bug (filtering on Python `@property` instead of DB field)
- **Not started**: Tests, production deployment config, search/filtering UI, property map integration, SEO metadata

## Known Bug (Fix Before Anything Else)

In `properties/views.py`, both `PropertyListView` and `PropertyDetailView` use:
```python
Property.objects.filter(is_published=True)
```
But `is_published` is a Python `@property` on the model, not a database field. This will raise a `FieldError`. The correct filter is:
```python
Property.objects.filter(status__is_published_status=True)
```

## What Likely Needs Doing Next

1. **Fix the `is_published` filter bug** in `properties/views.py` (both views)
2. **Add property search/filtering** — by location, property_type, listing_type, price range, bedrooms
3. **Add SEO fields** — meta title, meta description on Property (possibly via django-meta or manual fields)
4. **Populate seed data** — sample locations, amenities, statuses, properties for development
5. **Consider switching admin theme** — Jazzmin is currently configured but Django Unfold may have been considered (see decisions log)
6. **Add tests** — at minimum model tests for Property, Location hierarchy, status filtering
7. **Production hardening** — gunicorn, proper SECRET_KEY from env, HTTPS, ALLOWED_HOSTS

## What NOT To Do

1. **Do NOT upgrade to Django 5.x** — pinned `<5.0` for django-cms v4 compatibility
2. **Do NOT reorder INSTALLED_APPS** — `frontend_extensions` must be last (after all djangocms_frontend apps) or patches will not apply
3. **Do NOT remove `CMS_CONFIRM_VERSION4 = True`** — required for django-cms v4
4. **Do NOT replace django-parler with django-modeltranslation** for Property — parler is already integrated with TranslatableAdmin, custom change_form template, and URL routing by translated slug
5. **Do NOT use django-filer for PropertyImage** — deliberate decision to use plain ImageField (see DEC-006)
6. **Do NOT edit `frontend_extensions/forms.py`** — it is an intentional stub; all real form work is in `patches.py`
7. **Do NOT add fields to entangled forms by mutating `_meta.entangled_fields` at runtime** — you must create proper form subclasses or the metaclass assertion will crash

## Key Files to Know

| File | What it does |
|------|-------------|
| `mysite/settings.py` | All Django + CMS config. JAZZMIN_SETTINGS, CMS_TEMPLATES, PARLER_LANGUAGES |
| `properties/models.py` | Property, PropertyImage, Location (tree), Amenity, PropertyStatus |
| `properties/admin.py` | Rich admin with translatable tabs, sortable images, bulk upload |
| `properties/views.py` | **HAS A BUG** — public list/detail views |
| `frontend_extensions/patches.py` | All plugin monkey-patches (forms, render, fieldsets, attributes) |
| `services/models.py` | Service model with FilerImageField |
| `CHANGES.md` | Detailed file-by-file reference and change log |
| `docker-compose.yml` | Dev environment (web + db services) |
