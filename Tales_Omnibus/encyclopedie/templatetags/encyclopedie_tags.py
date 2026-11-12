from django import template

from encyclopedie.models import fiches_liees as chercher_fiches_liees

register = template.Library()


@register.inclusion_tag('encyclopedie/includes/fiches_liees.html')
def fiches_liees(page):
    """
    Encart « Fiches liées » en bas d'une fiche (Héros, Lieu, Événement, Lore) :
    {% load encyclopedie_tags %} puis {% fiches_liees page %}.
    """
    return {'fiches': chercher_fiches_liees(page)}
