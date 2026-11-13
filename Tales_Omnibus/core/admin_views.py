"""
La page « Entretien du site » de l'admin (Paramètres > Entretien du site).

Le même entretien que manage.py entretien (core/entretien.py), sans le
terminal : pour le MJ, après une grosse session d'ajouts. Sans migrations
(c'est l'affaire du développeur, au moment de la mise à jour du site).

Réservée aux administrateurs (superuser) : elle touche à tout le site.
Les boutons envoient le formulaire en POST : une action qui MODIFIE des
données ne doit jamais passer par un simple lien (GET), qu'un robot ou un
préchargement du navigateur pourrait déclencher.
"""
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse

from core.entretien import lancer_entretien, pages_a_publier

ACTIONS = {
    'simulation': "Vérification (rien n'a été modifié)",
    'entretien': "Entretien terminé",
    'publier': "Pages publiées et entretien terminé",
}


def entretien_du_site(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    action = request.POST.get('action') if request.method == 'POST' else None
    etapes = None
    if action in ACTIONS:
        etapes = lancer_entretien(
            simulation=(action == 'simulation'),
            migrer=False,
            publier=(action == 'publier'),
            utilisateur=request.user,  # l'historique des pages dira qui a publié
        )

    return TemplateResponse(request, "core/admin/entretien.html", {
        'etapes': etapes,
        'resultat': ACTIONS.get(action),
        'a_publier': list(pages_a_publier()),
    })
