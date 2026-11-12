from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from campagnes.models import CampagnePage, EvenementPage, HeroPage, LieuPage
from core.models import BaseFichePage


# 1. INDEX DE L'ENCYCLOPÉDIE : rassemble TOUTES les fiches taguables du site
class EncyclopedieIndexPage(Page):
    class Meta:
        verbose_name = "Encyclopédie"

    bandeau = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Image du bandeau",
        help_text="Grande image horizontale en haut de la page."
    )
    intro = RichTextField(
        blank=True,
        features=['bold', 'italic', 'link'],
        verbose_name="Accroche"
    )
    illustration = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Illustration",
        help_text="Image verticale affichée à côté des filtres."
    )

    subpage_types = ['encyclopedie.LorePage']
    parent_page_types = ['home.HomePage']
    max_count = 1  # Une seule encyclopédie pour tout l'univers

    content_panels = Page.content_panels + [
        FieldPanel('bandeau'),
        FieldPanel('intro'),
        FieldPanel('illustration'),
    ]

    @staticmethod
    def types_de_fiches():
        """
        Les types de pages qui apparaissent dans l'encyclopédie :
        { valeur dans l'URL : (modèle, libellé affiché) }.
        C'est une méthode et pas une constante car LorePage est définie
        plus bas dans ce fichier.
        """
        return {
            'heros': (HeroPage, "Héros"),
            'lieux': (LieuPage, "Lieux"),
            'evenements': (EvenementPage, "Événements"),
            'lore': (LorePage, "Lore"),
        }

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        types = self.types_de_fiches()
        accueil = self.get_parent()
        campagnes = CampagnePage.objects.live().descendant_of(accueil)

        # --- 1. Les filtres choisis, lus dans l'URL (?campagne=3&type=lieux&tag=dragon)
        #     Formulaire en GET : l'URL filtrée peut être partagée ou mise en favori.
        #     Une valeur inconnue est simplement ignorée (pas d'erreur 500).
        id_campagne = request.GET.get('campagne', '')
        campagne = campagnes.filter(pk=id_campagne).first() if id_campagne.isdigit() else None
        type_choisi = request.GET.get('type') if request.GET.get('type') in types else ''
        tag_choisi = request.GET.get('tag', '')

        # --- 2. Pour chaque type de fiche, une requête avec les filtres
        fiches = []
        tags_disponibles = {}
        for cle, (modele, libelle) in types.items():
            if type_choisi and cle != type_choisi:
                continue
            # Les fiches Lore sont communes à tout l'univers (elles ne sont
            # rangées dans aucune campagne) : un filtre de campagne les écarte.
            if campagne and modele is LorePage:
                continue
            racine = campagne or accueil
            requete = modele.objects.live().descendant_of(racine)

            # Les tags proposés = ceux des fiches AVANT le filtre de tag,
            # sinon il ne resterait que le tag cliqué et on ne pourrait plus en changer.
            for slug, nom in requete.filter(tags__isnull=False).values_list('tags__slug', 'tags__name'):
                tags_disponibles[slug] = nom

            if tag_choisi:
                requete = requete.filter(tags__slug=tag_choisi)

            for fiche in requete.prefetch_related('tags'):
                fiche.type_libelle = libelle  # affiché en badge sur la carte
                fiches.append(fiche)

        # Les 4 types sont mélangés : un seul tri alphabétique pour tout le monde
        fiches.sort(key=lambda fiche: fiche.title.lower())

        context.update({
            'fiches': fiches,
            'campagnes': campagnes,
            'types': {cle: libelle for cle, (_, libelle) in types.items()},
            'tags': sorted(tags_disponibles.items(), key=lambda tag: tag[1].lower()),
            'campagne_choisie': campagne,
            'type_choisi': type_choisi,
            'tag_choisi': tag_choisi,
        })
        return context


# 2. Modèle de Tag relié à la vraie classe LorePage (non-abstraite)
class LorePageTag(TaggedItemBase):
    content_object = ParentalKey(
        'LorePage',
        on_delete=models.CASCADE,
        related_name='tagged_items'
    )


# 3. FICHE LORE
class LorePage(BaseFichePage):
    class Meta:
        verbose_name = "Fiche Lore"
        verbose_name_plural = "Fiches Lore"

    tags = ClusterTaggableManager(through=LorePageTag, blank=True)

    subpage_types = []  # Page feuille
    parent_page_types = ['encyclopedie.EncyclopedieIndexPage']

    content_panels = BaseFichePage.content_panels + [
        FieldPanel('tags'),
    ]
