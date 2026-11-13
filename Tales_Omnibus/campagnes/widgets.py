"""Widgets d'admin pour les cartes."""
from django import forms


class OutilsDeCarteWidget(forms.Widget):
    """
    Le champ « forme » d'une Apparition, vu dans l'admin : la valeur (le JSON
    des sommets) est dans un <input type="hidden">, et à côté trois boutons :
    « Placer un point », « Tracer une zone », « Effacer ».

    Le travail se fait en JavaScript (editeur_carte.js) : les boutons
    activent l'image de la carte affichée plus haut (EditeurDeCartePanel),
    et chaque clic sur l'image remplit les champs de CETTE ligne.

    On hérite de forms.Widget et pas de HiddenInput : un HiddenInput est
    considéré comme « caché » par Wagtail, qui n'afficherait pas les boutons.
    """
    template_name = "campagnes/widgets/outils_de_carte.html"

    class Media:
        # Chargés une seule fois, même s'il y a 30 lieux sur la carte
        js = ["campagnes/js/editeur_carte.js"]
        css = {"all": ["campagnes/css/editeur_carte.css"]}
