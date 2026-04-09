# Active Context — Vertex CMS

> Last updated: 2026-04-08

## Current Focus

The project just completed a major feature addition: the **properties app** (commit `a7d1930`, 2026-04-08). This added ~1,835 lines across 20 files including:
- Full Property model with translations, images, locations, amenities, statuses
- Rich admin interface with tabbed form, sortable image inline, bulk upload popup
- Public list and detail views with templates
- Jazzmin admin theme integration

The project is in an **early build phase** — only 5 commits, the core CMS scaffolding plus two content apps (services, properties).

## What Was Just Done (Latest Commit)

- Added `properties/` app: `Property`, `PropertyImage`, `Location`, `AmenityCategory`, `Amenity`, `PropertyStatus` models
- Applied django-jazzmin as admin theme with full Vertex CMS branding config
- Custom admin change_form template for Property (nested parler language tabs inside Details tab)
- Bulk image upload popup (AJAX, drag-and-drop, 10MB limit)
- Fixed TemplateSyntaxError from multi-line `{# #}` comment containing block tag
- Added `django-parler` and `django-admin-sortable2` to requirements

## Potential Issues / Blockers

1. **PropertyListView has a bug** — `Property.objects.filter(is_published=True)` will not work because `is_published` is a Python `@property`, not a database field. The queryset filter should be `filter(status__is_published_status=True)` instead. This will cause a `FieldError` at runtime.
2. **PropertyDetailView has the same bug** — same `is_published=True` filter issue.
3. **No `.env.example` file exists** — README references it but it is not in the repo.
4. **SECRET_KEY in docker-compose.yml** — hardcoded `change-me-in-production-please`, fine for dev but needs .env for production.
5. **No tests** — `properties/tests.py` is the default Django stub (just `from django.test import TestCase`).
6. **No property templates in CMS_TEMPLATES** — properties use standalone Django views, not CMS pages. This is intentional but means properties cannot use CMS placeholders.

## Recent Changes (Git Log)

| Date       | Commit    | Summary                                                       |
|------------|-----------|---------------------------------------------------------------|
| 2026-04-08 | `a7d1930` | Add properties app, Jazzmin admin theme, fix template issues  |
| 2026-03-26 | `04ca2f9` | Initial commit (services app, frontend_extensions, CMS setup) |
| 2026-03-26 | `36e2435` | Initial commit                                                |
| 2026-03-26 | `a73e56a` | Initial commit after renaming to vertex-cms                   |
| 2026-03-26 | `d2e37cd` | Initial commit after renaming to vertex-cms                   |

## Active Assumptions

| #  | Assumption                                                   | Status       |
|----|--------------------------------------------------------------|--------------|
| A1 | Development is local Docker Compose only (no staging/prod)   | Assumed      |
| A2 | Single developer (or very small team) — no branch strategy   | Assumed      |
| A3 | English is the primary language; es/fr are planned but not populated | Assumed |
| A4 | Jazzmin theme is final choice (not switching to Unfold)      | Needs confirm|
| A5 | Property listing views need the `is_published` filter bug fixed before use | Confirmed bug |
