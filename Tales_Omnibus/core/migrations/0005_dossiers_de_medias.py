"""
SQUELETTE DE DOSSIERS pour les images et les documents.

Les « dossiers » de Wagtail sont les COLLECTIONS (Paramètres > Collections).
Elles servent à ranger les images ET les documents, et elles s'emboîtent.
Pour l'ALT automatique (core/images.py), le dossier d'une image dit ce
qu'elle montre : une image rangée dans « Personnage > Héros » aura pour ALT
« Personnage, Héros : <titre de l'image> ».

Cette migration crée un squelette d'exemple, pour que le MJ comprenne tout
de suite comment ranger. Il peut ensuite renommer, ajouter, supprimer.
  - Elle ne recrée pas un dossier qui existe déjà (relancer est sans effet).
  - Le retour arrière ne supprime RIEN : les dossiers peuvent contenir des
    images du client entre-temps.

Note technique : on importe le VRAI modèle Collection, pas la version
« historique » d'apps.get_model(). Les collections sont un arbre (django-
treebeard) : seule la vraie classe sait calculer les chemins (add_child).
"""
from django.db import migrations

# (nom, [sous-dossiers]) : noms au SINGULIER, ils sont lus dans l'ALT
SQUELETTE = [
    ("Personnage", ["Héros", "PNJ", "Déité", "Créature"]),
    ("Lieu", ["Carte", "Ville", "Paysage"]),
    ("Objet", []),
    ("Aide de jeu", []),   # handouts : lettres, plans, PDF à distribuer aux joueurs
    ("Site", []),          # logo, bannières, décor du site lui-même
]


def creer_les_dossiers(apps, schema_editor):
    from wagtail.models import Collection

    racine = Collection.get_first_root_node()
    if racine is None:  # base sans racine : Wagtail n'est pas encore installé
        return
    for nom, enfants in SQUELETTE:
        dossier = racine.get_children().filter(name=nom).first() or racine.add_child(name=nom)
        for nom_enfant in enfants:
            if not dossier.get_children().filter(name=nom_enfant).exists():
                dossier.add_child(name=nom_enfant)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_categories'),
        ('wagtailcore', '0098_apitoken'),
    ]

    operations = [
        migrations.RunPython(creer_les_dossiers, migrations.RunPython.noop),
    ]
