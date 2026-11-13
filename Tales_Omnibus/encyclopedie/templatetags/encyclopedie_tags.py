from django import template

from campagnes.models import LieuPage
from encyclopedie.models import etiqueter, fiches_liees as chercher_fiches_liees, ranger_par_famille

register = template.Library()


@register.inclusion_tag('encyclopedie/includes/fiches_liees.html')
def fiches_liees(page):
    """
    Encart « Fiches liées » en bas d'une fiche (Héros, Lieu, Événement, Lore) :
    {% load encyclopedie_tags %} puis {% fiches_liees page %}.
    """
    # Sur la fiche d'un lieu, l'encart « Liés à ce lieu » montre déjà ses
    # événements et ses héros : on ne les répète pas ici.
    deja_affichees = [fiche.pk for fiche in fiches_rattachees(page)] if isinstance(page, LieuPage) else []
    return {'fiches': chercher_fiches_liees(page, exclure=deja_affichees), 'titre': "Fiches liées"}


@register.inclusion_tag('encyclopedie/includes/fiches_liees.html')
def fiches_du_lieu(lieu):
    """
    Sur la fiche d'un lieu : les événements qui s'y sont passés (dans l'ordre
    chronologique) puis les héros qui en viennent. Ce sont les champs
    "lieu" / "lieu_origine" lus à l'envers, grâce à leur related_name.
    """
    return {'fiches': fiches_rattachees(lieu), 'titre': "Liés à ce lieu"}


def fiches_rattachees(lieu):
    """Événements du lieu (ordre chronologique) puis héros qui en viennent."""
    evenements = etiqueter(lieu.evenements.live().order_by('date_ordre'), 'evenements')
    heros = etiqueter(lieu.heros_originaires.live().order_by('title'), 'heros')
    return evenements + heros


@register.simple_tag
def tags_par_famille(tags):
    """
    Les tags d'une fiche, rangés par famille (voir ranger_par_famille) :
    {% tags_par_famille page.tags.all as groupes %}
    """
    return ranger_par_famille(tags)
