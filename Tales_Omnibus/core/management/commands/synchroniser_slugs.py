"""
Remet le slug de chaque page en accord avec son titre (ou son slug fixe) :
    ../env/Scripts/python.exe manage.py synchroniser_slugs

À lancer une fois après l'arrivée de SlugAutomatiqueMixin : les pages créées
avant gardent leur ancien slug tant qu'on ne les réenregistre pas. Ensuite,
c'est automatique à chaque enregistrement dans l'admin.

Comme ranger_lieux, c'est une commande et pas une migration : changer des
adresses de pages, c'est du CONTENU. Relancer la commande ne fait rien si
tout est déjà à jour.
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page

from core.slugs import SlugAutomatiqueMixin


class Command(BaseCommand):
    help = "Aligne les slugs des pages sur leur titre (ou leur slug fixe)."

    def handle(self, *args, **options):
        changements = 0
        # order_by("path") : les parents d'abord, pour que les URL des enfants
        # soient recalculées à partir de la nouvelle adresse du parent.
        ids = Page.objects.order_by("path").values_list("id", flat=True)
        for page_id in ids:
            # On recharge chaque page JUSTE avant de l'enregistrer : si son parent
            # vient de changer de slug, Wagtail a mis à jour son url_path en base,
            # et une copie chargée avant serait réenregistrée avec l'ancien.
            page = Page.objects.get(id=page_id).specific
            if not isinstance(page, SlugAutomatiqueMixin):
                continue
            ancien = page.slug
            # save() appelle full_clean(), qui recalcule le slug. Sur une page
            # publiée, Wagtail crée la redirection 301 depuis l'ancienne adresse.
            page.save()
            if page.slug != ancien:
                changements += 1
                self.stdout.write(self.style.SUCCESS(f"{page.title} : {ancien} -> {page.slug}"))
        if not changements:
            self.stdout.write("Tous les slugs sont déjà à jour.")
