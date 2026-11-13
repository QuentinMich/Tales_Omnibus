from django.apps import AppConfig


class CampagnesConfig(AppConfig):
    name = 'campagnes'

    def ready(self):
        # Branche les signaux (campagnes/signals.py : accès des comptes joueurs)
        from . import signals  # noqa: F401
