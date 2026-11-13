"""
RECHERCHE PLEIN TEXTE du site (/search/?query=…).

Wagtail cherche dans les champs déclarés dans les search_fields des modèles :
titre, accroche, articles et tags des fiches, texte des campagnes (voir
core/models.py et campagnes/models.py).

Chaque résultat est ensuite « habillé » comme une carte de l'encyclopédie :
son type (catégorie de la fiche, sinon le type de page), sa couleur, son
image et son accroche. L'accroche vient de core/seo.py : la même que la
méta description, déjà écrite pour Google. Rien de neuf à inventer.
"""
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from wagtail.models import Page

from core.models import NavigationSettings
from core.seo import description_seo, image_seo

RESULTATS_PAR_PAGE = 10


def habiller(page, nom_du_site):
    """Ajoute à la page ce qu'il faut pour l'afficher en carte de résultat."""
    page = page.specific
    categorie = getattr(page, 'categorie_effective', None)
    # Le type affiché : « Déité majeure », « Ville »… sinon « Campagne », « Carte »…
    page.libelle_type = categorie.nom if categorie else page._meta.verbose_name.capitalize()
    page.couleur = categorie.couleur_effective if categorie else ""
    page.image_resultat = image_seo(page)
    page.accroche = description_seo(page, nom_du_site)
    return page


def search(request):
    recherche = request.GET.get("query", "").strip()

    if recherche:
        # live() : pages publiées ; public() : pas les pages protégées par mot
        # de passe ; on retire la racine technique de Wagtail (depth 1)
        trouvees = Page.objects.live().public().filter(depth__gt=1).search(recherche)
        # Le moteur de Wagtail sous SQLite ne classe pas par pertinence. On le
        # fait nous-mêmes, simplement : les pages dont le TITRE contient le
        # mot cherché d'abord (« dragon » -> le Dragon de Suie en tête), puis
        # les autres. sorted() est « stable » : à égalité, l'ordre est gardé.
        mot = recherche.lower()
        resultats = sorted(trouvees, key=lambda page: mot not in page.title.lower())
    else:
        resultats = Page.objects.none()

    # get_page : une page hors limite (?page=999) renvoie la dernière page
    page_de_resultats = Paginator(resultats, RESULTATS_PAR_PAGE).get_page(request.GET.get("page"))

    # On n'habille QUE les 10 résultats affichés (pas les 200 trouvés)
    nom_du_site = NavigationSettings.load(request_or_site=request).site_name
    page_de_resultats.object_list = [habiller(page, nom_du_site) for page in page_de_resultats]

    return TemplateResponse(request, "search/search.html", {
        "search_query": recherche,
        "search_results": page_de_resultats,
        "nombre_de_resultats": page_de_resultats.paginator.count if recherche else 0,
    })
