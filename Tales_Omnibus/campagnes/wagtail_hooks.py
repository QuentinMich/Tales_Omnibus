"""
Raccourcis dans la barre latérale de l'admin : un menu "Univers" qui liste
directement toutes les campagnes, héros, lieux et événements (toutes
campagnes confondues), sans passer par l'explorateur de pages.
"""
from wagtail import hooks
from wagtail.admin.ui.tables import Column
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import CampagnePage, EvenementPage, HeroPage, LieuPage


class CampagneListingViewSet(PageListingViewSet):
    model = CampagnePage
    icon = "globe"
    menu_label = "Campagnes"
    columns = PageListingViewSet.columns + [
        Column("status", label="Statut", sort_key="status"),
    ]


class HeroListingViewSet(PageListingViewSet):
    model = HeroPage
    icon = "user"
    menu_label = "Héros"
    columns = PageListingViewSet.columns + [
        Column("joueur_nom", label="Joué par", sort_key="joueur_nom"),
    ]


class LieuListingViewSet(PageListingViewSet):
    model = LieuPage
    icon = "site"
    menu_label = "Lieux"
    columns = PageListingViewSet.columns + [
        Column("categorie", label="Catégorie"),
    ]


class EvenementListingViewSet(PageListingViewSet):
    model = EvenementPage
    icon = "date"
    menu_label = "Événements"
    columns = PageListingViewSet.columns + [
        Column("date_affichage", label="Date", sort_key="date_ordre"),
    ]


class UniversViewSetGroup(ViewSetGroup):
    """Regroupe les 4 listes sous un seul menu "Univers"."""
    menu_label = "Univers"
    menu_icon = "folder-open-inverse"
    menu_order = 150  # juste sous "Pages" dans la barre latérale
    items = (
        CampagneListingViewSet("liste_campagnes"),
        HeroListingViewSet("liste_heros"),
        LieuListingViewSet("liste_lieux"),
        EvenementListingViewSet("liste_evenements"),
    )


@hooks.register("register_admin_viewset")
def register_univers_menu():
    return UniversViewSetGroup()
