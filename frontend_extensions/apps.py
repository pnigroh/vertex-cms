from django.apps import AppConfig


class FrontendExtensionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "frontend_extensions"
    verbose_name = "Frontend Extensions"

    def ready(self):
        # Patch GridRowPlugin and other plugins that lack BackgroundMixin
        from . import patches  # noqa: F401
