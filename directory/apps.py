from django.apps import AppConfig


class DirectoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'directory'

    def ready(self):
        from . import signals  # noqa: F401
