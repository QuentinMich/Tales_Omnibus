"""
Range les fiches Lieu dans l'encyclopédie :
    ../env/Scripts/python.exe manage.py ranger_lieux

Avant la migration campagnes 0014, un lieu était une page ENFANT d'une carte.
Maintenant c'est une fiche universelle de l'encyclopédie, posée sur les
cartes par des Apparitions. La migration a déjà copié les coordonnées ;
cette commande déplace les pages elles-mêmes dans l'arbre.

Pas une migration : déplacer des pages, c'est du CONTENU, et les migrations
ne doivent toucher qu'à la STRUCTURE des tables. Relancer la commande ne
fait rien si tout est déjà rangé.
"""
from django.core.management.base import BaseCommand, CommandError

from campagnes.models import LieuPage
from encyclopedie.models import EncyclopedieIndexPage


class Command(BaseCommand):
    help = "Déplace les fiches Lieu (encore rangées sous une carte) dans l'encyclopédie."

    def handle(self, *args, **options):
        encyclopedie = EncyclopedieIndexPage.objects.first()
        if encyclopedie is None:
            raise CommandError("Crée d'abord la page Encyclopédie dans l'admin.")

        a_ranger = LieuPage.objects.not_child_of(encyclopedie)
        if not a_ranger.exists():
            self.stdout.write("Tous les lieux sont déjà dans l'encyclopédie.")
            return

        slugs_pris = set(encyclopedie.get_children().values_list('slug', flat=True))
        for lieu in a_ranger:
            if lieu.slug in slugs_pris:
                # Deux pages sœurs ne peuvent pas avoir la même adresse
                self.stderr.write(f"« {lieu.title} » : le slug « {lieu.slug} » existe déjà "
                                  "dans l'encyclopédie, change-le puis relance la commande.")
                continue
            ancienne_url = lieu.url
            # move() de Wagtail : met à jour l'arbre et les URL ; l'app redirects
            # crée une redirection automatique depuis l'ancienne adresse.
            lieu.move(encyclopedie, pos='last-child')
            slugs_pris.add(lieu.slug)
            self.stdout.write(self.style.SUCCESS(f"{lieu.title} : {ancienne_url} -> {LieuPage.objects.get(pk=lieu.pk).url}"))
