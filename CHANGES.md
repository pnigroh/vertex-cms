# Django CMS Customisation — File Reference & Change Log

This document lists every file created or modified during the setup of this
project, explains what each one does, and tells you exactly where to go to
change things.

---

## Project layout

```
djangocms-project/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
│
├── mysite/                     ← Django project package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── services/                   ← Custom "Services" content app
│   ├── models.py
│   ├── admin.py
│   ├── views.py
│   ├── urls.py
│   └── management/commands/create_superuser_auto.py
│
├── frontend_extensions/        ← Plugin behaviour extensions
│   ├── apps.py
│   ├── patches.py              ← ALL plugin customisation lives here
│   ├── forms.py                ← Stub (kept for theme compatibility)
│   └── frameworks/
│       └── bootstrap5.py       ← Theme render stubs
│
└── templates/
    ├── base.html
    ├── home.html
    ├── page.html
    ├── services.html
    └── services/
        ├── service_list.html
        └── service_detail.html
```

---

## File-by-file reference

---

### `Dockerfile`
Standard Python 3.11 slim image. Installs system libraries needed by
Pillow (jpeg, zlib, webp) and psycopg2. No customisation needed unless
you change the Python version or add system-level dependencies.

---

### `docker-compose.yml`
Defines two services:
- **db** — PostgreSQL 15
- **web** — the Django application

On startup the web container automatically runs `migrate`,
`create_superuser_auto`, `collectstatic`, then `runserver`.

**To change the default admin password** edit the `DJANGO_SUPERUSER_PASSWORD`
environment variable here (or in a `.env` file).

---

### `requirements.txt`
Python package pins. Notable entries:

| Package | Purpose |
|---|---|
| `django-cms` | Core CMS |
| `djangocms-frontend` | Bootstrap 5 plugin library |
| `djangocms-text-ckeditor` | Rich-text / HTML editing |
| `django-filer` | Image & file management |
| `djangocms-versioning` | Draft/publish workflow |
| `djangocms-alias` | Reusable content aliases |

---

### `mysite/settings.py`
Main Django settings. Key sections you may want to change:

| Setting | What it controls |
|---|---|
| `CMS_TEMPLATES` | Which page templates editors can choose. Add entries here when you create new templates in `templates/`. |
| `INSTALLED_APPS` | Add new Django apps here. `frontend_extensions` must stay **after** all `djangocms_frontend.*` apps. |
| `DJANGOCMS_FRONTEND_THEME` | Points to `"frontend_extensions"` — this is what activates all the plugin customisations. |
| `LANGUAGES` | Add languages here to enable multilingual content. |
| `THUMBNAIL_PROCESSORS` | Controls how filer resizes uploaded images. |

---

### `mysite/urls.py`
URL configuration. The `services/` URL prefix is registered here before the
CMS catch-all. If you rename or move the Services app, update this file.

---

### `services/models.py`  ⬅ **edit to change the Services data model**
Defines the `Service` model with these fields:

| Field | Type | Purpose |
|---|---|---|
| `title` | CharField | Headline |
| `slug` | SlugField | URL identifier |
| `intro` | TextField | Short teaser text |
| `content` | TextField | Full HTML body |
| `image` | FilerImageField | Main image (via django-filer) |
| `is_published` | BooleanField | Show/hide on the site |

After changing this file you must run `python manage.py makemigrations services`
inside the container.

---

### `services/admin.py`  ⬅ **edit to change how Services appear in Django admin**
Registers `Service` with a custom `ModelAdmin` that shows a thumbnail preview,
auto-fills the slug from the title, and groups fields into logical sections.

---

### `services/views.py` / `services/urls.py`
Standard Django class-based views (`ListView`, `DetailView`) and URL patterns
for the public Services pages (`/en/services/` and `/en/services/<slug>/`).

---

### `services/management/commands/create_superuser_auto.py`
Non-interactive superuser creation used by docker-compose on first boot.
Reads `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`,
`DJANGO_SUPERUSER_PASSWORD` from environment variables.

---

### `templates/base.html`  ⬅ **edit to change the global page layout**
The master template inherited by every page. Contains:
- Bootstrap 5 CDN links
- The Django CMS toolbar tag (`{% cms_toolbar %}`) — **must stay** for
  frontend editing to work
- The top navigation bar using `{% show_menu %}`
- The `{% render_block "css" %}` / `{% render_block "js" %}` sekizai hooks

---

### `templates/home.html` / `page.html` / `services.html`
Page templates selectable from the CMS page settings. Each defines
`{% placeholder %}` regions that editors can fill with plugins.
Add new templates here and register them in `settings.CMS_TEMPLATES`.

---

### `templates/services/service_list.html` / `service_detail.html`
Public-facing templates for the Services app. Uses Bootstrap 5 card grid.

---

## `frontend_extensions/` — The plugin customisation package

This is the most important directory if you want to change plugin behaviour.

---

### `frontend_extensions/apps.py`
The Django AppConfig. Its only job is to call `from . import patches` inside
`ready()` so all patches run exactly once at server startup, after all apps
and plugin classes are loaded.

**You never need to edit this file.**

---

### `frontend_extensions/patches.py`  ⬅ **the main file to edit for plugin behaviour**

This single file is responsible for all plugin customisations. It is heavily
commented. Here is a map of what lives where:

#### Form mixin classes (top of file, lines ~50–140)

```python
class ExtraClassesMixin(EntangledModelFormMixin): ...
class BackgroundImageMixin(_UpstreamBackgroundFormMixin): ...
```

- **`ExtraClassesMixin`** — adds the "Extra CSS classes" text input to every
  plugin form. To rename the field, change `label=`. To change the help text,
  change `help_text=`.

- **`BackgroundImageMixin`** — adds the full Background block (colour, opacity,
  shadow, image, size, position) to every plugin that does not already have it.
  
  To **add or remove background-size choices** edit `BACKGROUND_SIZE_CHOICES`.  
  To **add or remove background-position choices** edit `BACKGROUND_POSITION_CHOICES`.

#### `_patch_grid_row()` (lines ~145–165)
Adds `BackgroundMixin` (colour/opacity/shadow) to `GridRowPlugin`, which ships
without it upstream. You should not need to edit this.

#### `_extend_plugin_forms()` (lines ~170–210)
Iterates every registered djangocms-frontend plugin and replaces its form
class with a subclass that includes `ExtraClassesMixin` and
`BackgroundImageMixin`. This is automatic — you do not need to list plugins
individually.

#### `_apply_bg_image(instance)` (lines ~220–260)
Called at render time. Reads `background_image`, `background_size`, and
`background_position` from the plugin's saved config, resolves the filer
image to a URL, and writes a `style="background-image:url('…');…"` attribute
onto the outermost HTML element.

To **change the fallback size** (used when the editor leaves it blank), change
`or "cover"`.  
To **change the fallback position**, change `or "center center"`.

#### `_patch_render()` (lines ~263–290)
Hooks into `CMSUIPluginBase.render` (the base of every plugin). Applies:
1. `extra_classes` → `instance.add_classes()`
2. `background_context/opacity/shadow` → Bootstrap `bg-*`, `bg-opacity-*`,
   `shadow-*` classes (only for plugins that don't already have
   `BackgroundMixin` in their MRO)
3. Calls `_apply_bg_image(instance)`

#### `_patch_background_mixin_fieldsets()` (lines ~295–340)
Appends `background_image`, `background_size`, `background_position` to the
"Background" fieldset block that upstream `BackgroundMixin.get_fieldsets`
already creates for Container, Row, Column, and Card plugins.

#### `_patch_base_fieldsets()` (lines ~345–440)
Injects two fieldset blocks into every plugin's edit form:
1. **"Extra CSS classes"** — always added, for every plugin
2. **"Background"** — added for plugins that do NOT already have
   `BackgroundMixin` (those get it from `_patch_background_mixin_fieldsets`)

#### `_patch_get_attributes()` (lines ~445–475)
Replaces `AbstractFrontendUIItem.get_attributes()` to fix two upstream bugs:
- Missing space between `class="…"` and subsequent attributes
- `conditional_escape()` mangling single quotes inside `style="url('…')"`

---

### `frontend_extensions/forms.py`
An empty stub. Django CMS frontend expects the theme module
(`DJANGOCMS_FRONTEND_THEME`) to be importable as a package. The actual form
work is done in `patches.py`. You can safely ignore this file.

---

### `frontend_extensions/frameworks/bootstrap5.py`
Theme render mixin stubs. djangocms-frontend's `mixin_factory()` looks for
`{Name}RenderMixin` classes in this module and mixes them into plugin
renderers at import time (for the subset of plugins that use `mixin_factory`).

The `_ExtraClassesRenderMixin` here is an early-MRO hook for those plugins.
The base render patch in `patches.py` covers all plugins uniformly so the
stubs here are a belt-and-braces safety net.

**You do not need to edit this file** unless you want to add plugin-specific
render behaviour that only applies to one named plugin.

---

## Summary of all changes made

| # | What | File(s) changed | Why |
|---|---|---|---|
| 1 | New Django CMS project scaffolding | `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `manage.py`, `mysite/*` | Initial setup |
| 2 | Django CMS settings wired up | `mysite/settings.py` | `CMS_CONFIRM_VERSION4`, `DJANGOCMS_FRONTEND_THEME`, `SITE_ID`, thumbnail config, CMS middleware |
| 3 | URL configuration | `mysite/urls.py` | `i18n_patterns`, services prefix, media/static in DEBUG |
| 4 | Services content model | `services/models.py` | Custom model with intro, HTML content, filer image |
| 5 | Services admin | `services/admin.py` | Thumbnail preview, slug auto-fill, fieldset grouping |
| 6 | Services public views & URLs | `services/views.py`, `services/urls.py` | ListView + DetailView, `/en/services/` |
| 7 | Auto superuser on boot | `services/management/commands/create_superuser_auto.py` | Non-interactive first-run setup |
| 8 | Page templates | `templates/base.html`, `templates/home.html`, `templates/page.html`, `templates/services.html` | `{% cms_toolbar %}` added, Bootstrap 5, sekizai blocks |
| 9 | Services templates | `templates/services/service_list.html`, `templates/services/service_detail.html` | Public-facing Bootstrap card layout |
| 10 | Frontend extensions app created | `frontend_extensions/__init__.py`, `frontend_extensions/apps.py`, `frontend_extensions/forms.py`, `frontend_extensions/frameworks/bootstrap5.py` | App scaffold + theme stubs |
| 11 | **Extra CSS classes field** on every plugin | `frontend_extensions/patches.py` | `ExtraClassesMixin` + `_extend_plugin_forms` + `_patch_base_fieldsets` |
| 12 | **Background colour/opacity/shadow** on every plugin (not just Grid/Card) | `frontend_extensions/patches.py` | `BackgroundImageMixin` inherits `BackgroundFormMixin`; `_patch_render` applies classes |
| 13 | **Background image** on every plugin | `frontend_extensions/patches.py` | `BackgroundImageMixin.background_image` (FilerImageField); `_apply_bg_image` renders inline style |
| 14 | **Background size & position** on every plugin | `frontend_extensions/patches.py` | `BACKGROUND_SIZE_CHOICES`, `BACKGROUND_POSITION_CHOICES`; `_apply_bg_image` reads them |
| 15 | **Background colour/image on GridRow** (missing upstream) | `frontend_extensions/patches.py` | `_patch_grid_row` prepends `BackgroundMixin` + `BackgroundFormMixin` to GridRow |
| 16 | HTML attribute bug fix (style escaping + spacing) | `frontend_extensions/patches.py` | `_patch_get_attributes` replaces `AbstractFrontendUIItem.get_attributes` |
| 17 | `DJANGOCMS_FRONTEND_THEME` setting | `mysite/settings.py` | Activates `frontend_extensions` as the theme |
| 18 | `frontend_extensions` in INSTALLED_APPS | `mysite/settings.py` | Ensures `apps.py.ready()` fires |
