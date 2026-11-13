"""
Signaux de l'app campagnes : les accès des comptes joueurs (campagnes/joueurs.py).

À la PUBLICATION d'une fiche Héros (et pas à chaque brouillon) : c'est la
version en ligne qui décide qui a la main sur la fiche.
"""
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from wagtail.signals import page_published

from campagnes.joueurs import retirer_l_acces, synchroniser_l_acces
from campagnes.models import HeroPage


@receiver(page_published, sender=HeroPage)
def acces_du_joueur_a_la_publication(sender, instance, **kwargs):
    synchroniser_l_acces(instance)


@receiver(pre_delete, sender=HeroPage)
def acces_du_joueur_a_la_suppression(sender, instance, **kwargs):
    # pre_delete : AVANT la suppression, tant qu'on peut encore retrouver le
    # groupe de la fiche par sa permission sur la page
    retirer_l_acces(instance)
