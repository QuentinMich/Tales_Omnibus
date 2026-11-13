from django import template

from core.images import texte_alternatif

register = template.Library()


@register.filter
def alt_auto(image):
    """
    L'ALT construit à partir des dossiers, du titre et de la description
    de l'image (voir core/images.py) :
        {% load images_tags %}
        {% image page.main_image fill-600x850 alt=page.main_image|alt_auto %}
    """
    return texte_alternatif(image)
