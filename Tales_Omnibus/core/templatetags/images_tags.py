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


@register.filter
def rendu(image, filtre):
    """
    La version d'une image à un format donné PAR UNE VARIABLE :
        {% with logo_img=logo|rendu:taille %}…{{ logo_img.url }}…{% endwith %}
    Le tag {% image %} de Wagtail, lui, veut le format écrit en toutes
    lettres ({% image logo max-160x160 %}) : il ne lit pas une variable.
    """
    return image.get_rendition(filtre)
