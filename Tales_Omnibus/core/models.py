from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.snippets.models import register_snippet

from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, InlinePanel

from core.blocks import BaseStreamBlock
from core.slugs import SlugAutomatiqueMixin

# Liste unique des réseaux sociaux, partagée par le site et les fiches Héros
SOCIAL_PLATFORMS = [
    ('twitch', 'Twitch'),
    ('youtube', 'YouTube'),
    ('discord', 'Discord'),
    ('twitter', 'X / Twitter'),
    ('instagram', 'Instagram'),
    ('bluesky', 'Bluesky'),
    ('tiktok', 'TikTok'),
]

# Modèle pour chaque réseau social
class SocialMediaLink(Orderable):
    setting = ParentalKey(
        'NavigationSettings',
        related_name='social_links',
        on_delete=models.CASCADE
    )
    platform = models.CharField(
        max_length=50,
        choices=SOCIAL_PLATFORMS,
        verbose_name="Plateforme"
    )
    url = models.URLField(verbose_name="Lien du profil")

    panels = [
        FieldPanel('platform'),
        FieldPanel('url'),
    ]

# Thèmes disponibles : la clé est le nom du fichier static/css/themes/<clé>.css.
# Pour ajouter un thème : créer le fichier, puis l'ajouter ici (une migration
# suivra, car Django enregistre la liste des choix).
THEMES = [
    ("", "Aucun : structure du wireframe (gris et ocre)"),
    ("grimoire", "Grimoire : médiéval fantastique"),
]


@register_setting
class NavigationSettings(ClusterableModel, BaseGenericSetting):
    theme = models.CharField(
        max_length=50, blank=True, default="", choices=THEMES,
        verbose_name="Thème du site",
        help_text="Change les couleurs, les polices et les formes. La mise en page ne bouge pas.",
    )
    site_name = models.CharField(
        max_length=255, 
        default="Tales Omnibus", 
        verbose_name="Nom du site / Univers"
    )
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Logo du site"
    )
    logo_dore = models.BooleanField(
        default=False,
        verbose_name="Dorer le logo",
        help_text=(
            "Pour un logo d'UNE seule couleur sur fond transparent (idéalement un SVG) : "
            "sa silhouette est remplie avec la couleur du thème (la feuille d'or du "
            "Grimoire…). Un logo en couleurs ou sur fond plein deviendrait un simple aplat."
        ),
    )

    panels = [
        FieldPanel('site_name'),
        FieldPanel('logo'),
        FieldPanel('logo_dore'),
        FieldPanel('theme'),
        InlinePanel('social_links', label="Réseaux Sociaux"),
    ]

    class Meta:
        # Le nom affiché dans l'admin (menu, titre de la page). Le nom de la
        # CLASSE reste NavigationSettings : le changer obligerait à renommer
        # la table et toutes les références dans les templates.
        verbose_name = "Paramètres du site"
        verbose_name_plural = "Paramètres du site"

# --- CATÉGORIES : l'arborescence du SITE (ce que cherche le visiteur) -------
#
# Deux arbres différents dans Tales Omnibus :
#   - l'arbre des PAGES (Campagne > Héros, Encyclopédie > Lore…) range les
#     fiches pour l'ADMIN et donne les adresses ;
#   - l'arbre des CATÉGORIES (Personnage > Déité > Déité mineure) range les
#     fiches pour le VISITEUR. Il ne dépend pas du type de page : un PNJ est
#     une fiche Lore rangée dans « Personnage > PNJ ».
# Chaque fiche a UNE catégorie ; sans catégorie, elle tombe dans la catégorie
# « par défaut » de son type de page (ex. Lore -> « Divers »).

TYPES_DE_FICHES = [
    ('heros', "Héros"),
    ('lieux', "Lieux"),
    ('evenements', "Événements"),
    ('lore', "Lore"),
]


class CategorieForm(WagtailAdminModelForm):
    """Formulaire d'admin : pas de boucle dans l'arbre."""

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        ancetre = parent
        while ancetre is not None:
            # En remontant depuis le parent choisi, on ne doit jamais retomber
            # sur la catégorie elle-même (sinon : A rangée dans B rangée dans A)
            if self.instance.pk and ancetre.pk == self.instance.pk:
                raise ValidationError(
                    "Une catégorie ne peut pas être rangée dans elle-même "
                    "ou dans une de ses sous-catégories."
                )
            ancetre = ancetre.parent
        return parent

    def clean_par_defaut_pour(self):
        # Champ unique mais facultatif : deux "" seraient un doublon, deux None non
        return self.cleaned_data.get('par_defaut_pour') or None


@register_snippet
class Categorie(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    parent = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,  # supprimer « Personnage » remonte ses enfants à la racine
        related_name='enfants',
        verbose_name="Catégorie parente",
        help_text="Vide = catégorie principale (Personnage, Lieu…)."
    )
    icone = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Icône",
        help_text="Si vide, reprend celle de la catégorie parente."
    )
    couleur = models.CharField(
        max_length=7, blank=True,
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', "Code couleur au format #RRGGBB.")],
        verbose_name="Couleur",
        help_text="Code HEX (#3B6EA2). Si vide, reprend celle de la catégorie parente. "
                  "Sert aussi de couleur d'étoile sur les cartes pour les lieux."
    )
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    par_defaut_pour = models.CharField(
        max_length=20, choices=TYPES_DE_FICHES,
        null=True, blank=True, unique=True,  # une seule catégorie par défaut par type
        verbose_name="Catégorie par défaut pour",
        help_text="Les fiches de ce type SANS catégorie seront rangées ici."
    )

    base_form_class = CategorieForm
    panels = [
        FieldPanel('nom'),
        FieldPanel('parent'),
        FieldPanel('icone'),
        FieldPanel('couleur'),
        FieldPanel('ordre'),
        FieldPanel('par_defaut_pour'),
    ]

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def ancetres(self):
        """[Personnage, Déité, Déité mineure] pour « Déité mineure »."""
        chemin, categorie = [], self
        while categorie is not None:
            chemin.insert(0, categorie)
            categorie = categorie.parent
        return chemin

    def __str__(self):
        # Le chemin complet : c'est ce qui s'affiche dans le sélecteur de l'admin
        return " › ".join(c.nom for c in self.ancetres())

    @property
    def couleur_effective(self):
        """Sa couleur, sinon celle du plus proche ancêtre qui en a une."""
        return next((c.couleur for c in reversed(self.ancetres()) if c.couleur), "")

    @property
    def icone_effective(self):
        return next((c.icone for c in reversed(self.ancetres()) if c.icone_id), None)


def categories_en_memoire():
    """
    Toutes les catégories en UNE requête, avec leurs parents reliés en mémoire :
    ensuite ancetres(), couleur_effective… ne font plus aucune requête.
    (Il y en a quelques dizaines : les charger toutes coûte moins cher que
    de remonter l'arbre fiche par fiche.)
    """
    toutes = {c.pk: c for c in Categorie.objects.select_related('icone')}
    for categorie in toutes.values():
        categorie.parent = toutes.get(categorie.parent_id)  # remplit le cache du ForeignKey
    return toutes


def arbre_des_categories(toutes=None):
    """L'arbre « à plat », dans l'ordre d'affichage : [(categorie, profondeur), …]."""
    toutes = toutes or categories_en_memoire()
    enfants = {}
    for categorie in sorted(toutes.values(), key=lambda c: (c.ordre, c.nom.lower())):
        enfants.setdefault(categorie.parent_id, []).append(categorie)

    resultat = []

    def parcourir(parent_id, profondeur):
        for categorie in enfants.get(parent_id, []):
            resultat.append((categorie, profondeur))
            parcourir(categorie.pk, profondeur + 1)

    parcourir(None, 0)
    return resultat


def ids_de_la_branche(categorie, toutes=None):
    """La catégorie ET toutes ses sous-catégories (choisir Personnage = héros + PNJ + déités)."""
    toutes = toutes or categories_en_memoire()
    ids = {categorie.pk}
    while True:  # on descend niveau par niveau jusqu'à ne plus rien trouver
        nouveaux = {c.pk for c in toutes.values() if c.parent_id in ids} - ids
        if not nouveaux:
            return ids
        ids |= nouveaux


class BaseFichePage(SlugAutomatiqueMixin, Page):
    intro = RichTextField(
        blank=True,
        verbose_name="Présentation / Accroche",
        features=['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul']
    )
    main_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Image principale / Illustration"
    )
    body = StreamField(
        BaseStreamBlock(), 
        use_json_field=True, 
        blank=True,
        verbose_name="Contenu détaillé"
        )

    content_panels = Page.content_panels + [
        FieldPanel('main_image'),
        FieldPanel('intro'),
        FieldPanel('body'),
    ]

    # RECHERCHE : sans ça, Wagtail n'indexe que le titre. Avec, une fiche est
    # retrouvée par un mot de son accroche ou de ses articles.
    # (Après un ajout ici : manage.py update_index pour les pages existantes.)
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    class Meta:
        abstract = True

class FicheEncyclopedieMixin(models.Model):
    """
    Ce qu'ont en commun les fiches qui apparaissent dans l'encyclopédie
    (Héros, Lieu, Événement, Lore). Un "mixin" : un modèle abstrait qu'on
    ajoute en plus de BaseFichePage, pour que les Cartes et Chronologies
    (qui héritent aussi de BaseFichePage) n'aient pas cette case inutile.
    """
    epinglee = models.BooleanField(
        default=False,
        verbose_name="Épingler dans l'encyclopédie",
        help_text="Les fiches épinglées apparaissent en tête de liste."
    )
    categorie = models.ForeignKey(
        'core.Categorie',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Catégorie",
        help_text="Où ranger cette fiche pour le visiteur (ex : Personnage › PNJ). "
                  "Vide = la catégorie par défaut de ce type de fiche."
    )

    #: Clé du type de fiche ('heros', 'lieux'…), définie dans chaque modèle
    type_fiche = None

    # Les fiches de l'encyclopédie sont aussi retrouvées par leurs TAGS
    # (« dragon » trouve le Dragon de Suie, mais aussi la Nuit des Cendres).
    # Le mixin passe AVANT BaseFichePage dans l'héritage : c'est donc cette
    # liste qui compte, d'où le « BaseFichePage.search_fields + ».
    search_fields = BaseFichePage.search_fields + [
        index.RelatedFields('tags', [index.SearchField('name')]),
    ]

    class Meta:
        abstract = True

    @property
    def categorie_effective(self):
        """Sa catégorie, sinon la catégorie par défaut de son type de page."""
        return self.categorie or Categorie.objects.filter(par_defaut_pour=self.type_fiche).first()
