"""
ENTRETIEN DU SITE : tout ce qui garde le site propre, en une seule fois.

À lancer après un pull, ou après une grosse session d'archiviste (beaucoup
de fiches ajoutées, renommées, déplacées) :
  - en ligne de commande : manage.py entretien  (voir la commande)
  - dans l'admin : Paramètres > Entretien du site (bouton)

Chaque étape est une petite fonction qui renvoie un COMPTE RENDU (Etape) :
la commande l'écrit dans le terminal, l'admin l'affiche dans une page.
Une seule logique, deux façons de la lancer.

simulation=True : on ne modifie RIEN, on dit ce qu'on ferait.
"""
import io
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor
from wagtail.contrib.redirects.models import Redirect
from wagtail.images import get_image_model
from wagtail.models import Page

NOMBRE_DE_SAUVEGARDES_GARDEES = 10
MAX_NOMS_LISTES = 8  # dans le rapport, au-delà on écrit « … et 12 autres »


@dataclass
class Etape:
    titre: str
    lignes: list = field(default_factory=list)
    # a_verifier=True : rien n'a été changé, c'est une liste de choses que le
    # MJ devrait regarder (affichée en orange dans l'admin)
    a_verifier: bool = False

    def dire(self, texte):
        self.lignes.append(texte)
        return self


def resumer(noms):
    """['A', 'B', …] -> « A, B, C … et 4 autres »"""
    noms = list(noms)
    texte = ", ".join(noms[:MAX_NOMS_LISTES])
    if len(noms) > MAX_NOMS_LISTES:
        texte += f" … et {len(noms) - MAX_NOMS_LISTES} autres"
    return texte


def lancer_commande(nom, *args):
    """Lance une commande manage.py et renvoie ses lignes de sortie."""
    sortie = io.StringIO()
    call_command(nom, *args, stdout=sortie, stderr=sortie)
    return [ligne for ligne in sortie.getvalue().splitlines() if ligne.strip()]


# --------------------------------------------------------------- 0. sauvegarde
def sauvegarder_la_base(simulation=False):
    """
    Une copie datée de db.sqlite3 dans sauvegardes/ (ignoré par git).
    sqlite3.backup() et pas une simple copie de fichier : c'est la façon sûre
    de copier une base SQLite PENDANT qu'elle sert (le site tourne).
    """
    etape = Etape("Sauvegarde de la base")
    base = settings.DATABASES[DEFAULT_DB_ALIAS]
    chemin = Path(str(base.get('NAME', '')))
    if 'sqlite3' not in base.get('ENGINE', '') or not chemin.is_file():
        return etape.dire("Pas une base SQLite sur disque : sauvegarde à faire par l'hébergeur.")
    if simulation:
        return etape.dire("Une copie de la base serait faite dans sauvegardes/.")

    dossier = Path(settings.BASE_DIR) / "sauvegardes"
    dossier.mkdir(exist_ok=True)
    destination = dossier / f"db-{datetime.now():%Y-%m-%d-%H%M%S}.sqlite3"
    with sqlite3.connect(chemin) as source, sqlite3.connect(destination) as copie:
        source.backup(copie)
    # On ne garde que les plus récentes (les noms datés se trient tout seuls)
    for ancienne in sorted(dossier.glob("db-*.sqlite3"))[:-NOMBRE_DE_SAUVEGARDES_GARDEES]:
        ancienne.unlink()
    return etape.dire(f"Copie faite : sauvegardes/{destination.name}")


# --------------------------------------------------------------- 1. migrations
def migrations_en_attente():
    """Les migrations pas encore appliquées, sous la forme « app nom »."""
    executeur = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
    plan = executeur.migration_plan(executeur.loader.graph.leaf_nodes())
    return [f"{migration.app_label} {migration.name}" for migration, _ in plan]


def appliquer_les_migrations(simulation=False):
    etape = Etape("Migrations")
    noms = migrations_en_attente()
    if not noms:
        return etape.dire("La base est à jour.")
    if simulation:
        return etape.dire(f"{len(noms)} à appliquer : {resumer(noms)}")
    call_command("migrate", interactive=False, verbosity=0)
    return etape.dire(f"{len(noms)} appliquée(s) : {resumer(noms)}")


# --------------------------------------------------------------- 1 bis. publication
def pages_a_publier():
    """Les pages qui ont des modifications pas encore en ligne (ou jamais publiées)."""
    return Page.objects.filter(has_unpublished_changes=True, depth__gt=1).order_by("path")


def publier_les_brouillons(simulation=False, utilisateur=None):
    """
    « Tout publier » : publie la DERNIÈRE version de chaque page en attente.
    Pour 100 fiches créées d'un coup, plutôt que 100 clics sur « Publier ».
    order_by("path") : les parents avant leurs enfants.
    (Pour une page + ses enfants seulement : explorateur de pages, cocher la
    page, « Publier », case « inclure les sous-pages » : c'est natif Wagtail.)
    """
    etape = Etape("Publication des pages en attente")
    pages = list(pages_a_publier())
    if not pages:
        return etape.dire("Rien à publier : tout est en ligne.")
    if simulation:
        return etape.dire(f"{len(pages)} à publier : {resumer(p.title for p in pages)}")
    for page in pages:
        revision = page.get_latest_revision()
        if revision:
            revision.publish(user=utilisateur)
    return etape.dire(f"{len(pages)} publiée(s) : {resumer(p.title for p in pages)}")


# --------------------------------------------------------------- 2. lieux et slugs
def ranger_les_lieux(simulation=False):
    from campagnes.models import LieuPage
    from encyclopedie.models import EncyclopedieIndexPage
    etape = Etape("Lieux rangés dans l'encyclopédie")
    encyclopedie = EncyclopedieIndexPage.objects.first()
    if encyclopedie is None:
        return etape.dire("Pas encore de page Encyclopédie : rien à faire.")
    hors_place = LieuPage.objects.not_child_of(encyclopedie)
    if not hors_place.exists():
        return etape.dire("Tous les lieux sont à leur place.")
    if simulation:
        return etape.dire(f"À déplacer : {resumer(l.title for l in hors_place)}")
    etape.lignes += lancer_commande("ranger_lieux")
    return etape


def synchroniser_les_slugs(simulation=False):
    from core.slugs import SlugAutomatiqueMixin
    etape = Etape("Adresses des pages (slugs)")
    if not simulation:
        lignes = lancer_commande("synchroniser_slugs")
        etape.lignes += lignes or ["Tous les slugs sont déjà à jour."]
        return etape
    # Simulation : on recalcule le slug en mémoire, sans enregistrer
    a_changer = []
    for page in Page.objects.order_by("path").specific():
        if isinstance(page, SlugAutomatiqueMixin):
            ancien = page.slug
            try:
                page.full_clean()
            except Exception:
                continue
            if page.slug != ancien:
                a_changer.append(f"{page.title} ({ancien} -> {page.slug})")
    return etape.dire(f"À renommer : {resumer(a_changer)}" if a_changer else "Tous les slugs sont déjà à jour.")


# --------------------------------------------------------------- 3. géographie
def recalculer_la_geographie(simulation=False):
    """« Situé dans » : refait l'arbre de chaque carte publiée."""
    from campagnes.models import CartePage
    etape = Etape("Géographie des cartes")
    total = 0
    for carte in CartePage.objects.live():
        changes = carte.ranger_les_lieux(enregistrer=not simulation)
        if changes:
            total += changes
            etape.dire(f"{carte.title} : {changes} lieu(x) {'à replacer' if simulation else 'replacé(s)'}")
    if not total:
        etape.dire("Toutes les cartes sont à jour.")
    return etape


# --------------------------------------------------------------- 4. redirections
def nettoyer_les_redirections(simulation=False):
    """
    Les redirections que Wagtail crée quand une page change d'adresse
    s'accumulent. Trois cas :
      - INUTILE : l'ancienne adresse est de nouveau celle d'une vraie page
        (la page est revenue à son ancien nom) : la redirection la masquerait
        ou ferait une boucle -> supprimée ;
      - EN CHAÎNE (redirections tapées à la main) : /a -> /b, et /b -> /c.
        On fait sauter l'étape : /a -> /c ;
      - vers une page DÉPUBLIÉE : signalée seulement (elle peut revenir).
    """
    etape = Etape("Redirections")
    adresses_des_pages = {
        Redirect.normalise_path(page.url)
        for page in Page.objects.live().filter(depth__gt=1)
        if page.url
    }
    redirections = list(Redirect.objects.select_related('redirect_page'))
    # normalise_path des DEUX côtés : « /saison-1/ » et « /saison-1 » sont la
    # même adresse (une redirection tapée à la main peut garder le « / »)
    par_adresse = {Redirect.normalise_path(r.old_path): r for r in redirections}

    inutiles = [r for r in redirections if Redirect.normalise_path(r.old_path) in adresses_des_pages]
    for redirection in inutiles:
        etape.dire(f"Inutile (une page vit de nouveau ici) : {redirection.old_path}")
        if not simulation:
            redirection.delete()

    for redirection in redirections:
        if redirection in inutiles or not redirection.redirect_link.startswith("/"):
            continue
        # On suit la chaîne jusqu'au bout (vus : sécurité contre les boucles)
        cible, vus = redirection, {redirection.pk}
        while cible.redirect_link and Redirect.normalise_path(cible.redirect_link) in par_adresse:
            suivante = par_adresse[Redirect.normalise_path(cible.redirect_link)]
            if suivante.pk in vus:
                break
            vus.add(suivante.pk)
            cible = suivante
        if cible is not redirection:
            etape.dire(f"Chaîne raccourcie : {redirection.old_path} -> {cible.link}")
            if not simulation:
                redirection.redirect_page = cible.redirect_page
                redirection.redirect_link = cible.redirect_link
                redirection.save()

    depubliees = [r.old_path for r in redirections if r.redirect_page and not r.redirect_page.live]
    if depubliees:
        etape.dire(f"Mènent à une page dépubliée (gardées) : {resumer(depubliees)}")
    if not etape.lignes:
        etape.dire(f"{len(redirections)} redirection(s), toutes utiles.")
    return etape


# --------------------------------------------------------------- 5 et 6. index
def reconstruire_les_index(simulation=False):
    etape = Etape("Index (références et recherche)")
    if simulation:
        return etape.dire("Seraient reconstruits : l'index des références et celui de la recherche.")
    # Références : évite le plantage connu quand on supprime une page encore
    # citée par un champ disparu (voir CLAUDE.md, « Pièges connus »)
    lancer_commande("rebuild_references_index")
    lancer_commande("update_index")
    return etape.dire("Index des références et index de recherche reconstruits.")


# --------------------------------------------------------------- 7. rapport
TITRE_DE_FICHIER = re.compile(r"_|\d{3,}|^(img|dsc|image|designer|screenshot)", re.IGNORECASE)


# --------------------------------------------------------------- plan du site
def verifier_le_plan_du_site(simulation=False):
    """
    Le plan du site (sitemap.xml) et robots.txt se calculent à chaque visite :
    rien à régénérer. On vérifie seulement ce qu'ils annoncent, et surtout
    l'ADRESSE du site : c'est elle que le plan donne aux moteurs de recherche.
    """
    from django.urls import reverse
    from wagtail.contrib.sitemaps.sitemap_generator import Sitemap
    from wagtail.models import Site

    etape = Etape("Référencement (sitemap.xml et robots.txt)")
    site = Site.objects.filter(is_default_site=True).select_related("root_page").first()
    if site is None:
        etape.a_verifier = True
        return etape.dire("Aucun site par défaut : Paramètres avancés > Sites.")

    nombre = Sitemap().items().count()  # sans requête : le site par défaut
    racine = site.root_url
    etape.dire(f"{nombre} page(s) publique(s) dans sitemap.xml : {racine}{reverse('plan_du_site')}")
    etape.dire(f"robots.txt ({racine}{reverse('robots_txt')}) : tout est ouvert aux moteurs "
               "sauf l'admin et la recherche, et il indique l'adresse du plan.")
    etape.dire("Toujours à jour : publier ou dépublier une page la retire ou l'ajoute tout de suite.")
    if site.hostname in ("localhost", "127.0.0.1"):
        # Pas bloquant pendant le développement, mais à ne pas oublier
        etape.a_verifier = True
        etape.dire(f"L'adresse du site est encore « {site.hostname} » : avant la mise en ligne, "
                   "mettre le vrai nom de domaine dans Paramètres avancés > Sites, sinon le plan "
                   "du site enverra les moteurs de recherche vers localhost.")
    return etape


def rapport_a_verifier():
    """Rien n'est modifié ici : la liste de ce que le MJ devrait regarder."""
    from campagnes.models import LieuPage
    etape = Etape("À vérifier", a_verifier=True)
    Image = get_image_model()

    sans_dossier = Image.objects.filter(collection__depth=1).order_by('title')
    if sans_dossier:
        etape.dire(f"Images sans dossier (ALT moins précis) : {resumer(i.title for i in sans_dossier)}")
    noms_bruts = [i.title for i in Image.objects.order_by('title') if TITRE_DE_FICHIER.search(i.title)]
    if noms_bruts:
        etape.dire(f"Images au titre de fichier brut (à renommer pour l'ALT) : {resumer(noms_bruts)}")

    lieux_sans_carte = LieuPage.objects.live().filter(apparitions__isnull=True).order_by('title')
    if lieux_sans_carte:
        etape.dire(f"Lieux posés sur aucune carte : {resumer(l.title for l in lieux_sans_carte)}")

    brouillons = pages_a_publier()
    if brouillons:
        etape.dire(f"Modifications pas encore publiées : {resumer(p.title for p in brouillons)}")

    if not etape.lignes:
        etape.dire("Rien à signaler. Bravo !")
    return etape


# --------------------------------------------------------------- tout
def lancer_entretien(simulation=False, migrer=True, sauvegarder=True, publier=False, utilisateur=None):
    """
    Lance toutes les étapes, dans l'ordre, et renvoie leurs comptes rendus.
    migrer=False : depuis l'admin (une migration est l'affaire du développeur).
    publier=True : publie d'abord tout ce qui attend (jamais par défaut).
    """
    etapes = []
    if sauvegarder:
        etapes.append(sauvegarder_la_base(simulation))
    if migrer:
        etapes.append(appliquer_les_migrations(simulation))
    # Si des migrations attendent et qu'on ne les applique pas (simulation, ou
    # bouton de l'admin), la suite lirait des colonnes qui n'existent pas
    # encore en base : on s'arrête là, avec une explication plutôt qu'un crash.
    if (simulation or not migrer) and migrations_en_attente():
        etapes.append(Etape("Arrêt", a_verifier=True).dire(
            "Des migrations attendent : la suite ne peut pas être vérifiée avant. "
            "Lancer « manage.py entretien » (sans --simulation) pour les appliquer."
        ))
        return etapes
    if publier:
        # Avant le reste : slugs, géographie et recherche se calculent sur
        # le contenu publié
        etapes.append(publier_les_brouillons(simulation, utilisateur))
    for fonction in (ranger_les_lieux, synchroniser_les_slugs, recalculer_la_geographie,
                     nettoyer_les_redirections, reconstruire_les_index, verifier_le_plan_du_site):
        etapes.append(fonction(simulation))
    etapes.append(rapport_a_verifier())
    return etapes
