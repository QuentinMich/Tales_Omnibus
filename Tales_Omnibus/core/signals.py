"""
SIGNAUX : du code lancé automatiquement quand quelque chose arrive.

Index de recherche et tags. À la publication, Wagtail enregistre la page et
met son index de recherche à jour TOUT DE SUITE ; mais les tags (des
« enfants » de la page, gérés par modelcluster) ne sont écrits en base
qu'APRÈS. Résultat : l'index était calculé sans les nouveaux tags, et un tag
ajouté n'était trouvable qu'à la publication suivante.

Le signal page_published, lui, part une fois la publication TERMINÉE (tags
compris) : on y recalcule l'index de la page.
"""
from django.dispatch import receiver
from wagtail.search import index
from wagtail.signals import page_published


@receiver(page_published)
def reindexer_apres_publication(sender, instance, **kwargs):
    index.insert_or_update_object(instance)
