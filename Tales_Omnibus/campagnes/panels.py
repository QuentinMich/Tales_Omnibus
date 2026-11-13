"""Panneaux d'admin propres aux campagnes."""
from django.urls import reverse
from wagtail.admin.panels import Panel


class EditeurDeCartePanel(Panel):
    """
    Dans le formulaire d'une Carte : l'image de la carte, en grand, avec
    tous les lieux déjà posés (points et zones). C'est la « table de
    travail » des boutons Placer / Tracer de chaque lieu.

    Panneau en lecture seule (comme ChildPagesPanel) : il n'ajoute aucun
    champ au formulaire. L'image est demandée par le JavaScript à une petite
    vue d'admin (voir wagtail_hooks.image_de_carte) : si on change l'image
    de la carte dans le formulaire, l'éditeur suit sans recharger la page.
    """

    class BoundPanel(Panel.BoundPanel):
        template_name = "campagnes/panels/editeur_carte.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            # L'adresse de la vue, avec un 0 à la place de l'id de l'image :
            # le JS remplace ce 0 par l'image choisie.
            context["url_image"] = reverse("image_de_carte", args=[0])
            return context
