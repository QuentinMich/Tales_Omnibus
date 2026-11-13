"""
Ajouts de l'app core à l'admin Wagtail : la page « Entretien du site »,
dans le menu Paramètres (core/admin_views.py, core/entretien.py).
"""
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from core.admin_views import entretien_du_site


@hooks.register("register_admin_urls")
def urls_entretien():
    return [path("entretien/", entretien_du_site, name="entretien_du_site")]


class MenuReserveAuxAdministrateurs(MenuItem):
    """L'entrée n'apparaît que pour un superuser (la page le vérifie aussi)."""

    def is_shown(self, request):
        return request.user.is_superuser


@hooks.register("register_settings_menu_item")
def menu_entretien():
    return MenuReserveAuxAdministrateurs(
        "Entretien du site", reverse("entretien_du_site"), icon_name="cog", order=10000,
    )
