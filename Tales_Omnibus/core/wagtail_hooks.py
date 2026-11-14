"""
Ajouts de l'app core à l'admin Wagtail :
  - la page « Entretien du site » (core/admin_views.py, core/entretien.py) ;
  - le MENU DE GAUCHE réorganisé pour quelqu'un qui ne connaît rien au code.

Le menu est réorganisé par le hook construct_main_menu, appelé à CHAQUE
affichage : on renomme, on réordonne, on regroupe les entrées existantes.
Aucune app n'est modifiée : si une mise à jour de Wagtail ajoute une entrée,
elle apparaît simplement en plus, sans rien casser.
"""
import copy

from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem, settings_menu

from core.admin_views import bien_demarrer, entretien_du_site


@hooks.register("register_admin_urls")
def urls_entretien():
    return [
        path("entretien/", entretien_du_site, name="entretien_du_site"),
        path("bien-demarrer/", bien_demarrer, name="bien_demarrer"),
    ]


class MenuReserveAuxAdministrateurs(MenuItem):
    """L'entrée n'apparaît que pour un superuser (la page le vérifie aussi)."""

    def is_shown(self, request):
        return request.user.is_superuser


@hooks.register("register_admin_menu_item")
def menu_bien_demarrer():
    # Tout en haut du menu : c'est la première chose à faire sur un site neuf
    return MenuReserveAuxAdministrateurs(
        "Bien démarrer", reverse("bien_demarrer"), name="bien-demarrer", icon_name="circle-check", order=1,
    )


@hooks.register("register_settings_menu_item")
def menu_entretien():
    return MenuReserveAuxAdministrateurs(
        "Entretien du site", reverse("entretien_du_site"), icon_name="cog", order=10000,
    )


# --------------------------------------------------------------------- MENU
class LienVersUnFragment(MenuItem):
    """
    Lien DIRECT vers la liste d'un fragment (Catégories…), au lieu de passer
    par la page « Fragments » qui demande d'abord de choisir un type.
    N'apparaît que si la personne a le droit de voir ce fragment.
    """

    def __init__(self, label, modele, **kwargs):
        self.modele = modele
        app, nom = modele._meta.app_label, modele._meta.model_name
        super().__init__(label, reverse(f"wagtailsnippets_{app}_{nom}:list"), **kwargs)

    def is_shown(self, request):
        app, nom = self.modele._meta.app_label, self.modele._meta.model_name
        return any(request.user.has_perm(f"{app}.{action}_{nom}") for action in ("view", "add", "change"))


def renomme(entree, libelle, ordre, icone=None):
    """
    Une COPIE de l'entrée, avec un autre libellé et une autre place.
    Copie : les entrées de Wagtail sont partagées par tous les visiteurs de
    l'admin, on ne modifie pas l'original.
    """
    entree = copy.copy(entree)
    entree.label, entree.order = libelle, ordre
    if icone:
        entree.icon_name = icone
    return entree


def sous_menu(libelle, nom, icone, ordre, entrees):
    """Un sous-menu qui regroupe des entrées existantes (vide = invisible)."""
    return SubmenuMenuItem(libelle, Menu(items=[e for e in entrees if e]), name=nom,
                           icon_name=icone, order=ordre)


@hooks.register("construct_main_menu")
def organiser_le_menu(request, menu_items):
    from core.models import Categorie
    from encyclopedie.models import FamilleDeTags
    from pages.models import Prestation

    principal = {entree.name: entree for entree in menu_items}
    # Les entrées du sous-menu « Paramètres » de Wagtail, si la personne a le
    # droit de les voir (is_shown) : on va les ranger ailleurs
    reglages = {e.name: e for e in settings_menu.registered_menu_items if e.is_shown(request)}

    def depuis(source, nom, libelle, ordre, icone=None):
        entree = source.get(nom)
        return renomme(entree, libelle, ordre, icone) if entree else None

    nouveau = [
        principal.get("bien-demarrer"),                            # réservé aux administrateurs
        depuis(principal, "explorer", "Plan du site", 100, "site"),
        principal.get("univers"),                                  # Campagnes, Héros, Lieux, Événements
        depuis(reglages, "collections", "Dossiers", 200, "folder-open-1"),
        principal.get("images"),
        principal.get("documents"),
        sous_menu("Organisation", "organisation", "list-ul", 500, [
            LienVersUnFragment("Catégories", Categorie, icon_name="folder-inverse"),
            LienVersUnFragment("Familles de tags", FamilleDeTags, icon_name="tag"),
            LienVersUnFragment("Prestations", Prestation, icon_name="pick"),
        ]),
        depuis(principal, "forms", "Messages", 600, "mail"),
        sous_menu("Comptes", "comptes", "group", 700, [
            depuis(reglages, "users", "Utilisateurs", 1),
            depuis(reglages, "groups", "Groupes", 2),
        ]),
        depuis(reglages, "parametres-du-site", "Paramètres du site", 800, "cogs"),  # nom tiré du verbose_name
        depuis(reglages, "entretien-du-site", "Entretien du site", 900, "cog"),
        principal.get("reports"),                                  # Rapports (Wagtail)
        sous_menu("Paramètres avancés", "parametres-avances", "warning", 10000, [
            depuis(reglages, "sites", "Sites", 1),
            depuis(reglages, "redirects", "Redirections", 2),
            depuis(reglages, "workflows", "Workflows", 3),
            depuis(reglages, "workflow-tasks", "Tâches de workflow", 4),
        ]),
        principal.get("help"),                                     # Aide (Wagtail)
    ]
    # Une entrée qu'on ne connaît pas (ajoutée par une mise à jour de Wagtail
    # ou une nouvelle app) n'est pas perdue : elle se range avant la fin.
    # « snippets » et « settings » sont remplacés par Organisation, Comptes…
    connues = {"bien-demarrer", "explorer", "univers", "images", "documents", "forms", "reports", "help", "snippets", "settings"}
    inconnues = [entree for nom, entree in principal.items() if nom not in connues]

    # On remplace le contenu de la liste reçue (Wagtail lit CETTE liste).
    # Un sous-menu dont toutes les entrées sont interdites disparaît tout seul.
    menu_items[:] = [entree for entree in nouveau + inconnues if entree and entree.is_shown(request)]
