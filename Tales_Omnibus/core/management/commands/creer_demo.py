"""
Crée (ou retire) la CAMPAGNE DE DÉMONSTRATION :
    ../env/Scripts/python.exe manage.py creer_demo
    ../env/Scripts/python.exe manage.py creer_demo --supprimer

Toute la logique est dans core/demo.py, partagée avec la page « Bien
démarrer » de l'admin (boutons Ajouter / Retirer la démo).
"""
from django.core.management.base import BaseCommand, CommandError

from core.demo import DemoImpossible, creer_demo, supprimer_demo


class Command(BaseCommand):
    help = "Crée (ou supprime avec --supprimer) une campagne de démonstration."

    def add_arguments(self, parser):
        parser.add_argument('--supprimer', action='store_true', help="Retire tout le contenu de démo.")

    def handle(self, *args, **options):
        try:
            message = supprimer_demo() if options['supprimer'] else creer_demo()
        except DemoImpossible as erreur:
            raise CommandError(str(erreur)) from erreur
        self.stdout.write(self.style.SUCCESS(message))
