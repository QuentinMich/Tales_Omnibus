from django import template
from wagtail.models import Site

from campagnes.models import CampagnesIndexPage
from encyclopedie.models import EncyclopedieIndexPage

register = template.Library()


@register.inclusion_tag('core/includes/main_menu.html', takes_context=True)
def main_menu(context):
    """
    Menu principal avec des LIBELLÉS FIXES.

    Chaque entrée garde toujours le même mot ("Campagnes", "Encyclopédie"...),
    quel que soit le titre de la page dans l'admin. La page est retrouvée par
    son TYPE (ou par le choix fait sur la page d'accueil), pas par son titre
    ni son slug : renommer une page ne casse donc jamais le menu.
    """
    request = context['request']
    accueil = Site.find_for_request(request).root_page.specific

    # getattr(..., None) : si la racine du site n'est pas une HomePage
    # (cas des tests du starter), on n'affiche juste pas ces liens.
    entrees = [
        ("Accueil", accueil),
        ("Univers", getattr(accueil, 'page_univers', None)),  # choisie sur la page d'accueil
        ("Campagnes", CampagnesIndexPage.objects.live().descendant_of(accueil).first()),
        ("Encyclopédie", EncyclopedieIndexPage.objects.live().descendant_of(accueil).first()),
        ("Contact", getattr(accueil, 'page_contact', None)),  # choisie sur la page d'accueil
    ]

    page_courante = context.get('page')
    items = []
    for libelle, page in entrees:
        if page is None or not page.live:
            continue  # page pas encore créée ou dépubliée : on n'affiche pas de lien cassé
        if page_courante is None:
            actif = False
        elif page.pk == accueil.pk:
            actif = page_courante.pk == accueil.pk  # sinon l'accueil serait "actif" partout
        else:
            # Actif sur la page elle-même ET sur ses sous-pages
            # (une fiche Héros allume "Campagnes")
            actif = page_courante.url_path.startswith(page.url_path)
        items.append({
            'libelle': libelle,
            'page': page,
            'actif': actif,  # surlignage visuel (page ou une de ses sous-pages)
            'courant': page_courante is not None and page.pk == page_courante.pk,  # pour aria-current
        })

    return {'items': items}
