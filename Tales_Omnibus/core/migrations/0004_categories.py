"""
CategorieLieu devient Categorie : l'arbre des catégories du site.

Écrite à la main : makemigrations ne devine pas qu'il s'agit d'un RENOMMAGE
(trop de champs changent en même temps). Il aurait créé une table vide et
supprimé l'ancienne, et les lieux auraient perdu leur catégorie.
Ici, RenameModel garde la table et ses lignes : « Village » garde son id,
donc la ForeignKey des lieux pointe toujours au bon endroit.
"""
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def ranger_sous_lieu(apps, schema_editor):
    """
    Les anciennes catégories de lieu (Village…) deviennent des sous-catégories
    d'une catégorie principale « Lieu », qui sert aussi de catégorie par défaut
    des fiches Lieu.
    """
    Categorie = apps.get_model('core', 'Categorie')
    anciennes = list(Categorie.objects.all())
    lieu, _ = Categorie.objects.get_or_create(
        par_defaut_pour='lieux', defaults={'nom': "Lieu", 'ordre': 2},
    )
    for categorie in anciennes:
        if categorie.pk != lieu.pk:
            categorie.parent = lieu
            categorie.save(update_fields=['parent'])


def remettre_a_plat(apps, schema_editor):
    """Retour arrière : on retire la catégorie « Lieu » ajoutée par la migration."""
    Categorie = apps.get_model('core', 'Categorie')
    Categorie.objects.filter(par_defaut_pour='lieux', nom="Lieu").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_socialmedialink_platform'),
        ('wagtailimages', '0001_initial'),
        # Sur une base NEUVE, le renommage doit attendre les anciennes migrations
        # de campagnes qui pointent encore vers « core.categorielieu » (0008…) :
        # sinon elles ne trouvent plus le modèle et tout plante.
        ('campagnes', '0014_apparitions'),
    ]

    operations = [
        migrations.RenameModel('CategorieLieu', 'Categorie'),
        migrations.RenameField('categorie', 'couleur_marqueur', 'couleur'),
        migrations.AlterField(
            model_name='categorie',
            name='couleur',
            field=models.CharField(
                blank=True, max_length=7, verbose_name='Couleur',
                help_text="Code HEX (#3B6EA2). Si vide, reprend celle de la catégorie parente. "
                          "Sert aussi de couleur d'étoile sur les cartes pour les lieux.",
                validators=[django.core.validators.RegexValidator('^#[0-9A-Fa-f]{6}$', 'Code couleur au format #RRGGBB.')],
            ),
        ),
        migrations.AlterField(
            model_name='categorie',
            name='icone',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='+', to='wagtailimages.image', verbose_name='Icône',
                help_text='Si vide, reprend celle de la catégorie parente.',
            ),
        ),
        migrations.AddField(
            model_name='categorie',
            name='parent',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='enfants', to='core.categorie', verbose_name='Catégorie parente',
                help_text='Vide = catégorie principale (Personnage, Lieu…).',
            ),
        ),
        migrations.AddField(
            model_name='categorie',
            name='ordre',
            field=models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage"),
        ),
        migrations.AddField(
            model_name='categorie',
            name='par_defaut_pour',
            field=models.CharField(
                blank=True, null=True, unique=True, max_length=20,
                choices=[('heros', 'Héros'), ('lieux', 'Lieux'), ('evenements', 'Événements'), ('lore', 'Lore')],
                verbose_name='Catégorie par défaut pour',
                help_text='Les fiches de ce type SANS catégorie seront rangées ici.',
            ),
        ),
        migrations.AlterModelOptions(
            name='categorie',
            options={'ordering': ['ordre', 'nom'], 'verbose_name': 'Catégorie', 'verbose_name_plural': 'Catégories'},
        ),
        migrations.RunPython(ranger_sous_lieu, remettre_a_plat),
    ]
