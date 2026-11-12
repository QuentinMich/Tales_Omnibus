from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.snippets.models import register_snippet

from wagtail.models import Orderable, Page
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel

from core.blocks import BaseStreamBlock

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

@register_setting
class NavigationSettings(ClusterableModel, BaseGenericSetting):
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

    panels = [
        FieldPanel('site_name'),
        FieldPanel('logo'),
        InlinePanel('social_links', label="Réseaux Sociaux"),
    ]

@register_snippet
class CategorieLieu(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    icone = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Icône / Picto de carte"
    )
    couleur_marqueur = models.CharField(
        max_length=7,
        default="#FF0000",
        verbose_name="Couleur du marqueur (Code HEX)",
        help_text="Ex: #FF0000 pour rouge, #00FF00 pour vert..."
    )

    panels = [
        FieldPanel('nom'),
        FieldPanel('icone'),
        FieldPanel('couleur_marqueur'),
    ]

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Catégorie de lieu"
        verbose_name_plural = "Catégories de lieux"

class BaseFichePage(Page):
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

    class Meta:
        abstract = True
