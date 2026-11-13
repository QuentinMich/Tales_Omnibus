"""
COMPTES JOUEURS : un joueur peut modifier SA fiche Héros, et rien d'autre.

Côté MJ, deux gestes :
  1. Comptes > Utilisateurs > Ajouter : le compte du joueur (identifiant,
     mail, mot de passe), sans rien cocher d'autre ;
  2. sur la fiche Héros, champ « Compte du joueur », puis Publier.

Le site fait le reste à la publication (signal dans campagnes/signals.py) :
  - le compte entre dans le groupe « Joueurs » : se connecter à l'admin et
    envoyer des images (son portrait) ;
  - un groupe propre à la fiche, « Fiche : Brann le Rouquin », reçoit le
    droit de MODIFIER et PUBLIER cette page seulement, et le compte y entre.
Retirer le compte de la fiche (ou supprimer la fiche) retire l'accès.

Pourquoi un groupe par fiche ? Wagtail donne les droits sur une page à des
GROUPES, jamais à une personne directement (GroupPagePermission).
"""
from django.contrib.auth.models import Group, Permission
from wagtail.models import Collection, GroupCollectionPermission, GroupPagePermission

GROUPE_DES_JOUEURS = "Joueurs"
PREFIXE_GROUPE_FICHE = "Fiche : "


def permission(app, codename):
    return Permission.objects.get(content_type__app_label=app, codename=codename)


def groupe_des_joueurs():
    """Le groupe commun : accès à l'admin + images (envoyer, choisir)."""
    groupe, cree = Group.objects.get_or_create(name=GROUPE_DES_JOUEURS)
    if cree:
        groupe.permissions.add(permission("wagtailadmin", "access_admin"))
        racine = Collection.get_first_root_node()
        for codename in ("add_image", "choose_image"):
            GroupCollectionPermission.objects.get_or_create(
                group=groupe, collection=racine, permission=permission("wagtailimages", codename))
    return groupe


def groupe_de_la_fiche(hero, creer=True):
    """Le groupe « Fiche : … » de ce héros (retrouvé par sa permission sur la page)."""
    lien = (GroupPagePermission.objects
            .filter(page=hero, group__name__startswith=PREFIXE_GROUPE_FICHE)
            .select_related('group').first())
    if lien:
        groupe = lien.group
    elif creer:
        groupe = Group.objects.create(name=f"{PREFIXE_GROUPE_FICHE}{hero.title} (n°{hero.pk})")
        for codename in ("change_page", "publish_page"):
            GroupPagePermission.objects.create(group=groupe, page=hero,
                                               permission=permission("wagtailcore", codename))
    else:
        return None
    # Le nom suit le titre de la fiche (n° : deux héros peuvent avoir le même nom)
    nom = f"{PREFIXE_GROUPE_FICHE}{hero.title} (n°{hero.pk})"
    if groupe.name != nom:
        groupe.name = nom
        groupe.save(update_fields=['name'])
    return groupe


def quitter_les_joueurs_si_plus_de_fiche(utilisateur, sauf=None):
    """
    Plus aucune fiche ? Le compte perd aussi l'accès à l'admin.
    sauf : une fiche à ne pas compter (celle qu'on est en train de supprimer :
    pendant pre_delete, elle est encore en base).
    """
    from campagnes.models import HeroPage
    fiches = HeroPage.objects.filter(compte_joueur=utilisateur)
    if sauf is not None:
        fiches = fiches.exclude(pk=sauf.pk)
    if not fiches.exists():
        utilisateur.groups.remove(groupe_des_joueurs())


def synchroniser_l_acces(hero):
    """Met les droits en accord avec le champ « Compte du joueur » de la fiche."""
    joueur = hero.compte_joueur
    groupe = groupe_de_la_fiche(hero, creer=joueur is not None)
    if groupe is None:
        return
    anciens = list(groupe.user_set.exclude(pk=joueur.pk) if joueur else groupe.user_set.all())
    groupe.user_set.set([joueur] if joueur else [])
    if joueur:
        joueur.groups.add(groupe_des_joueurs())
    for ancien in anciens:  # le joueur d'avant, remplacé ou retiré
        quitter_les_joueurs_si_plus_de_fiche(ancien)


def retirer_l_acces(hero):
    """La fiche est supprimée : son groupe disparaît, son joueur perd l'accès."""
    groupe = groupe_de_la_fiche(hero, creer=False)
    if groupe is None:
        return
    anciens = list(groupe.user_set.all())
    groupe.delete()
    for ancien in anciens:
        quitter_les_joueurs_si_plus_de_fiche(ancien, sauf=hero)
