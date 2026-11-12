from django import template
from wagtail.models import Site

from campagnes.models import CampagnesIndexPage
from encyclopedie.models import EncyclopedieIndexPage
from pages.models import UniversPage

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
        ("Univers", UniversPage.objects.live().descendant_of(accueil).first()),
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


# Pour les rubriques, le lien retour garde un libellé fixe, comme le menu.
# Les autres pages (une campagne, une carte...) gardent leur titre.
RETOURS_FIXES = {
    CampagnesIndexPage: "aux campagnes",
    EncyclopedieIndexPage: "à l'encyclopédie",
}


@register.inclusion_tag('core/includes/back_link.html', takes_context=True)
def back_link(context):
    """
    Lien « ← Retour à ... » vers la page PARENTE dans l'arborescence.
    On n'utilise pas l'historique du navigateur : si on arrive d'un lien
    externe (Discord, Google...), « page précédente » sortirait du site.
    """
    page = context.get('page')
    accueil = Site.find_for_request(context['request']).root_page
    if page is None or page.pk == accueil.pk:
        return {}  # pas de lien retour sur l'accueil (ni sur la recherche)

    parent = page.get_parent().specific
    if parent.pk == accueil.pk:
        texte = "à l'accueil"
    else:
        texte = RETOURS_FIXES.get(type(parent), f"à {parent.title}")
    return {'parent': parent, 'texte': texte}
