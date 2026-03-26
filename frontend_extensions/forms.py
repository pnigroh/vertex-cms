"""
Theme form mixins for djangocms-frontend.

Loaded as `{DJANGOCMS_FRONTEND_THEME}.forms` by djangocms-frontend's
`get_forms(module)` factory. Any `{Name}FormMixin` defined here is mixed
into the corresponding plugin's form class at import time (only for plugins
that use `mixin_factory("Name")` in their form definition).

The actual heavy lifting — adding extra_classes and background_image to
every plugin form — is done in patches.py by replacing plugin.form with a
proper subclass. These lightweight stubs exist only because djangocms-frontend
expects the theme module to be importable and may look for named mixins.
"""
# Nothing needed here — patches.py handles all form extensions uniformly.
