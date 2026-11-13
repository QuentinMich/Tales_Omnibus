from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Branche les signaux (core/signals.py) au démarrage de Django.
        # L'import suffit : le décorateur @receiver fait le branchement.
        from . import signals  # noqa: F401
