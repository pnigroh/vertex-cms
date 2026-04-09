# Project DNA — Vertex CMS

## Identity

| Field         | Value                                                        |
|---------------|--------------------------------------------------------------|
| Project name  | Vertex CMS                                                   |
| Repo          | `pnigroh/vertex-cms` (GitHub)                                |
| Type          | Real-estate CMS — property listings + services + CMS pages   |
| Primary language | Python 3.11                                               |
| Framework     | Django 4.2.x (pinned `>=4.2,<5.0`)                          |
| CMS layer     | django-cms 4.1+ (v4 confirmed via `CMS_CONFIRM_VERSION4`)   |
| Frontend      | Bootstrap 5 (CDN), djangocms-frontend 1.3+                  |
| Admin theme   | django-jazzmin 3.0+ (replaced default admin)                |
| Database      | PostgreSQL 15 (Docker) / SQLite fallback (local dev)         |
| Static files  | WhiteNoise (CompressedStaticFilesStorage)                    |
| Translations  | django-parler (model-level), django-cms i18n (page-level)    |
| Image mgmt    | django-filer 3.0+ / easy-thumbnails 2.8+                    |
| Deployment    | Docker Compose (2-service: `web` + `db`)                     |

## Stack — Exact Version Pins (requirements.txt)

| Package                   | Version constraint |
|---------------------------|--------------------|
| Django                    | `>=4.2,<5.0`       |
| django-cms                | `>=4.1`            |
| djangocms-frontend        | `>=1.3`            |
| djangocms-text-ckeditor   | `>=5.1`            |
| django-filer              | `>=3.0`            |
| easy-thumbnails           | `>=2.8`            |
| djangocms-alias           | `>=2.0`            |
| djangocms-versioning      | `>=2.0`            |
| Pillow                    | `>=10.0`           |
| psycopg2-binary           | `>=2.9`            |
| whitenoise                | `>=6.6`            |
| django-sekizai            | `>=4.0`            |
| django-admin-sortable2    | `>=2.1`            |
| django-jazzmin            | `>=3.0`            |

## Hard Constraints

1. **Django 4.2 LTS only** — pinned `<5.0` in requirements.txt. Do not upgrade to Django 5.x without verifying django-cms v4 compatibility.
2. **django-cms v4 confirmation flag** — `CMS_CONFIRM_VERSION4 = True` in settings. This is required.
3. **`frontend_extensions` must be last in INSTALLED_APPS** — it monkey-patches all djangocms-frontend plugin forms/renders in `apps.py -> ready()`. If loaded before the plugins, patches fail silently.
4. **Entangled forms** — djangocms-frontend stores plugin config in a JSON `config` field via `django-entangled`. Form mixins must be proper subclasses (not runtime mutations) because `EntangledFormMetaclass.__new__` asserts fields exist in `base_fields`.
5. **Property translations via django-parler** — the Property model uses `TranslatedFields` for title/slug/description. Queries must use `.translated(lang)` or `.active_translations()`.
6. **Property images use plain ImageField** (not django-filer) — uploaded to `media/listing/<property_id>/`. The Service model uses `FilerImageField`.
7. **Location hierarchy via treebeard MP_Node** — materialized-path tree, not MPTT. Uses `movenodeform_factory` in admin.
8. **Property status is a separate model, not an enum** — `PropertyStatus` with `is_published_status` boolean controls public visibility.
9. **3 languages configured** — en, es, fr. Parler fallback is English.
10. **Docker Compose runs `create_superuser_auto` on every boot** — idempotent management command in `services/management/commands/`.

## Architecture Decisions

| ID      | Date       | Decision                                           | Rationale                                                                                   |
|---------|------------|----------------------------------------------------|---------------------------------------------------------------------------------------------|
| ADR-001 | 2026-03-26 | Use django-cms v4 as the CMS layer                 | Page-level content management with versioning, aliases, and Bootstrap 5 plugin library       |
| ADR-002 | 2026-03-26 | djangocms-frontend for all Bootstrap 5 UI plugins  | Grid, cards, accordion, tabs, etc. as CMS plugins rather than raw HTML                      |
| ADR-003 | 2026-03-26 | Monkey-patch plugin forms via `frontend_extensions` | Add extra_classes + background_image to every plugin without forking djangocms-frontend      |
| ADR-004 | 2026-03-26 | Docker Compose for development deployment          | Single `docker-compose up --build` to get PostgreSQL + Django running                       |
| ADR-005 | 2026-04-08 | django-jazzmin as admin theme                      | Modern admin UI with sidebar, icons, branding; replaces default Django admin                 |
| ADR-006 | 2026-04-08 | django-parler for Property translations            | Model-level i18n (title, slug, description) independent of CMS page translations            |
| ADR-007 | 2026-04-08 | treebeard MP_Node for Location hierarchy           | Country > State > City > Neighborhood tree; materialized-path for efficient ancestor queries |
| ADR-008 | 2026-04-08 | PropertyStatus as editable model (not enum)        | Client can add/rename statuses; `is_published_status` flag controls public visibility       |
| ADR-009 | 2026-04-08 | adminsortable2 for PropertyImage ordering          | Drag-and-drop image reordering in inline admin                                              |
| ADR-010 | 2026-04-08 | Bulk image upload via custom admin popup            | Multi-file upload with AJAX, 10MB limit, auto-ordering                                     |
