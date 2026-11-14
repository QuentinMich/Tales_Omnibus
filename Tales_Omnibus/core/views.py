"""
Vues publiques de core : le fichier robots.txt.

Le plan du site (sitemap.xml) vient de wagtail.contrib.sitemaps : il est
calculé À CHAQUE VISITE à partir des pages publiées. Il est donc toujours à
jour, sans rien régénérer : publier une page l'y ajoute, la dépublier l'en
retire.
"""
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET

# Les parties du site que les moteurs de recherche n'ont pas à explorer
ZONES_PRIVEES = ["/admin/", "/django-admin/", "/search/"]


def contenu_robots_txt(adresse_du_plan):
    """Le texte du robots.txt (partagé avec l'entretien, qui l'affiche)."""
    lignes = ["User-agent: *"]
    lignes += [f"Disallow: {chemin}" for chemin in ZONES_PRIVEES]
    lignes += ["", f"Sitemap: {adresse_du_plan}"]
    return "\n".join(lignes) + "\n"


@require_GET
def robots_txt(request):
    # Adresse ABSOLUE du plan : c'est ce que demandent les moteurs de recherche
    adresse_du_plan = request.build_absolute_uri(reverse("plan_du_site"))
    return HttpResponse(contenu_robots_txt(adresse_du_plan), content_type="text/plain; charset=utf-8")
