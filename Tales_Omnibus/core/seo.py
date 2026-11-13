"""
SEO AUTOMATIQUE : balise <title> et méta description générées pour chaque page.

Le client peut toujours tout écrire lui-même (onglet « Promotion » de l'admin :
« Titre de la page » et « Description de recherche »). S'il laisse vide, le
site construit tout seul :
  - le titre : « Vaël, déesse des Brumes · Déité majeure | Tales Omnibus »
    (titre de la page, sa catégorie, nom de l'univers) ;
  - la description : l'accroche de la page, sans HTML, coupée proprement à
    155 caractères (au-delà, Google la tronque de toute façon).

Fonctions « pures » (une page en entrée, du texte en sortie) : faciles à
tester, et utilisées par le tag {% seo_de_la_page %} dans base.html.
"""
import html
import re

from django.utils.html import strip_tags

LONGUEUR_DESCRIPTION = 155

# Les champs où chercher une accroche, dans l'ordre (le premier rempli gagne) :
# intro (fiches, encyclopédie, contact, univers), card_description et synopsis
# (campagnes), mj_presentation (page Univers).
CHAMPS_DESCRIPTION = ('intro', 'card_description', 'synopsis', 'mj_presentation')


def texte_brut(valeur):
    """'<p>Elle tisse&nbsp;le <b>brouillard</b></p>' -> 'Elle tisse le brouillard'."""
    texte = html.unescape(strip_tags(str(valeur or "")))
    return re.sub(r"\s+", " ", texte).strip()


def couper(texte, longueur=LONGUEUR_DESCRIPTION):
    """Coupe à la fin d'un mot, jamais au milieu, et ajoute « … »."""
    if len(texte) <= longueur:
        return texte
    coupe = texte[:longueur - 1].rsplit(" ", 1)[0]
    return coupe.rstrip(" ,;:.-–—") + "…"


def est_accueil(page):
    # depth 1 = racine technique de Wagtail, depth 2 = page d'accueil du site
    return page.depth <= 2


def titre_seo(page, nom_du_site):
    if page is None:
        return nom_du_site
    if page.seo_title:
        titre = page.seo_title
    elif est_accueil(page):
        return nom_du_site  # l'accueil, c'est le site lui-même
    else:
        titre = page.title
        categorie = getattr(page, 'categorie_effective', None)
        if categorie:
            titre = f"{titre} · {categorie.nom}"
    return f"{titre} | {nom_du_site}" if nom_du_site else titre


def description_seo(page, nom_du_site):
    if page is None:
        return ""
    if page.search_description:
        return page.search_description
    for champ in CHAMPS_DESCRIPTION:
        texte = texte_brut(getattr(page, champ, ""))
        if texte:
            return couper(texte)
    # Rien à reprendre : une phrase construite avec ce qu'on sait de la page
    categorie = getattr(page, 'categorie_effective', None)
    if categorie:
        return f"{page.title} : {categorie.nom.lower()} de l'univers {nom_du_site}."
    return f"{page.title}, sur {nom_du_site}." if not est_accueil(page) else f"L'univers de jeu de rôle {nom_du_site}."


def image_seo(page):
    """L'image de partage (Open Graph) : celle de la page si elle en a une."""
    for champ in ('main_image', 'banner_image', 'bandeau', 'hero_image', 'mj_image'):
        image = getattr(page, champ, None)
        if image:
            return image
    return None
