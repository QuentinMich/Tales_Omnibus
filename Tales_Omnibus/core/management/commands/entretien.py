"""
ENTRETIEN DU SITE, en une commande :
    ../env/Scripts/python.exe manage.py entretien
    ../env/Scripts/python.exe manage.py entretien --simulation   (ne change rien)
    ../env/Scripts/python.exe manage.py entretien --publier      (publie d'abord tout ce qui attend)

Dans l'ordre : sauvegarde de la base, migrations, lieux rangés, slugs,
géographie des cartes, ménage des redirections, index (références et
recherche), puis un rapport « à vérifier ».

À lancer après un pull, ou après une grosse session d'ajouts. Relancer ne
fait rien si tout est déjà propre. La logique est dans core/entretien.py,
partagée avec le bouton de l'admin (Paramètres > Entretien du site).
"""
from django.core.management.base import BaseCommand

from core.entretien import lancer_entretien


class Command(BaseCommand):
    help = "Sauvegarde, migre, aligne slugs/lieux/géographie, nettoie les redirections, réindexe."

    def add_arguments(self, parser):
        parser.add_argument('--simulation', action='store_true',
                            help="Affiche ce qui serait fait, sans rien modifier.")
        parser.add_argument('--publier', action='store_true',
                            help="Publie d'abord toutes les pages qui ont des modifications en attente.")
        parser.add_argument('--sans-sauvegarde', action='store_true',
                            help="Ne pas copier la base avant de commencer.")

    def handle(self, *args, **options):
        simulation = options['simulation']
        if simulation:
            self.stdout.write(self.style.WARNING("SIMULATION : rien ne sera modifié.\n"))

        for etape in lancer_entretien(simulation=simulation, publier=options['publier'],
                                      sauvegarder=not options['sans_sauvegarde']):
            style = self.style.WARNING if etape.a_verifier else self.style.MIGRATE_HEADING
            self.stdout.write(style(f"— {etape.titre}"))
            for ligne in etape.lignes:
                self.stdout.write(f"   {ligne}")

        self.stdout.write(self.style.SUCCESS("\nEntretien terminé." if not simulation else "\nSimulation terminée."))
