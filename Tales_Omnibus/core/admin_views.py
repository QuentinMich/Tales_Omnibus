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


# ------------------------------------------------------------------ Bien démarrer
def bien_demarrer(request):
    """
    La page « Bien démarrer » : créer la structure fixe du site en un clic,
    ajouter ou retirer la démo. Réservée aux administrateurs.

    Après chaque action : un message, puis une REDIRECTION vers la page
    (Post/Redirect/Get) : recharger la page ne relance pas l'action.
    """
    from django.contrib import messages
    from django.shortcuts import redirect

    from core.demo import (
        CAMPAGNE, DemoImpossible, creer_demo, demo_installee, images_de_demo_disponibles, supprimer_demo,
    )
    from core.structure_du_site import creer_structure, etat_de_la_structure, structure_complete

    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'structure':
                for ligne in creer_structure(utilisateur=request.user):
                    messages.success(request, ligne)
            elif action == 'demo_ajouter':
                messages.success(request, creer_demo())
            elif action == 'demo_retirer':
                messages.success(request, supprimer_demo())
        except DemoImpossible as erreur:
            messages.error(request, str(erreur))
        return redirect('bien_demarrer')

    presentes, attendues = images_de_demo_disponibles()
    return TemplateResponse(request, "core/admin/bien_demarrer.html", {
        'pages_fixes': etat_de_la_structure(),
        'structure_complete': structure_complete(),
        'demo_installee': demo_installee(),
        'nom_de_la_demo': CAMPAGNE,
        'images_presentes': presentes,
        'images_attendues': attendues,
    })
