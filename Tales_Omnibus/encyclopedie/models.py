from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from campagnes.models import CampagnePage, CartePage, EvenementPage, HeroPage, LieuPage
from core.slugs import SlugAutomatiqueMixin
from core.models import BaseFichePage, CategorieLieu, FicheEncyclopedieMixin


# 1. INDEX DE L'ENCYCLOPÉDIE : rassemble TOUTES les fiches taguables du site
class EncyclopedieIndexPage(SlugAutomatiqueMixin, Page):
    slug_fixe = "encyclopedie"

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

    subpage_types = ['encyclopedie.LorePage', 'campagnes.LieuPage']
    parent_page_types = ['home.HomePage']
    max_count = 1  # Une seule encyclopédie pour tout l'univers

    content_panels = Page.content_panels + [
        FieldPanel('bandeau'),
        FieldPanel('intro'),
        FieldPanel('illustration'),
    ]

    FICHES_PAR_PAGE = 12  # pagination : on n'affiche pas 200 fiches d'un coup

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        types = types_de_fiches()
        accueil = self.get_parent()
        campagnes = CampagnePage.objects.live().descendant_of(accueil)

        # --- 1. Les filtres choisis, lus dans l'URL (?campagne=3&type=lieux&tag=dragon)
        #     Formulaire en GET : l'URL filtrée peut être partagée ou mise en favori.
        #     Une valeur inconnue est simplement ignorée (pas d'erreur 500).
        id_campagne = request.GET.get('campagne', '')
        campagne = campagnes.filter(pk=id_campagne).first() if id_campagne.isdigit() else None
        type_choisi = request.GET.get('type') if request.GET.get('type') in types else ''
        tag_choisi = request.GET.get('tag', '')
        # La catégorie n'a de sens que pour les lieux : ignorée pour les autres types
        id_categorie = request.GET.get('categorie', '') if type_choisi == 'lieux' else ''

        # --- 2. Pour chaque type de fiche, une requête avec les filtres
        fiches = []
        tags_disponibles = {}
        categories = CategorieLieu.objects.none()
        for cle, requete in requetes_de_fiches(accueil, campagne, type_choisi):
            # Les tags proposés = ceux des fiches AVANT le filtre de tag,
            # sinon il ne resterait que le tag cliqué et on ne pourrait plus en changer.
            for slug, nom in requete.filter(tags__isnull=False).values_list('tags__slug', 'tags__name'):
                tags_disponibles[slug] = nom

            if cle == 'lieux':
                # Catégories proposées : seulement celles des lieux affichables
                # (pas de catégorie vide dans le menu).
                categories = CategorieLieu.objects.filter(lieux__in=requete).distinct().order_by('nom')
                if id_categorie.isdigit():
                    requete = requete.filter(categorie_id=id_categorie)

            if tag_choisi:
                requete = requete.filter(tags__slug=tag_choisi)
            fiches += etiqueter(requete, cle)

        # Les 4 types sont mélangés : un seul tri pour tout le monde,
        # les fiches épinglées d'abord, puis par ordre alphabétique.
        fiches.sort(key=lambda fiche: (not fiche.epinglee, fiche.title.lower()))

        # --- 3. Pagination : Django découpe la liste en pages de 12.
        #     get_page() est tolérant : ?page=abc ou ?page=999 donne une page valide.
        page_de_fiches = Paginator(fiches, self.FICHES_PAR_PAGE).get_page(request.GET.get('page'))

        context.update({
            'fiches': page_de_fiches,
            'campagnes': campagnes,
            'types': {cle: libelle for cle, (_, libelle) in types.items()},
            'tags': sorted(tags_disponibles.items(), key=lambda tag: tag[1].lower()),
            'campagne_choisie': campagne,
            'type_choisi': type_choisi,
            'categories': categories,
            'categorie_choisie': int(id_categorie) if id_categorie.isdigit() else None,
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
class LorePage(FicheEncyclopedieMixin, BaseFichePage):
    class Meta:
        verbose_name = "Fiche Lore"
        verbose_name_plural = "Fiches Lore"

    tags = ClusterTaggableManager(through=LorePageTag, blank=True)

    subpage_types = []  # Page feuille
    parent_page_types = ['encyclopedie.EncyclopedieIndexPage']

    content_panels = BaseFichePage.content_panels + [
        FieldPanel('tags'),
        FieldPanel('epinglee'),
    ]


# 4. OUTILS PARTAGÉS : utilisés par l'encyclopédie ET par les "fiches liées"
#    en bas de chaque fiche (encyclopedie/templatetags/encyclopedie_tags.py).
#    Écrits une seule fois ici pour que les deux affichent les fiches pareil.

def types_de_fiches():
    """
    Les types de pages qui apparaissent dans l'encyclopédie :
    { clé (dans l'URL et le CSS) : (modèle, libellé affiché) }.
    """
    return {
        'heros': (HeroPage, "Héros"),
        'lieux': (LieuPage, "Lieux"),
        'evenements': (EvenementPage, "Événements"),
        'lore': (LorePage, "Lore"),
    }


def requetes_de_fiches(accueil, campagne=None, type_choisi=''):
    """
    Une requête par type de fiche : les pages publiées sous l'accueil
    (ou sous une campagne). Renvoie des paires (clé du type, requête).
    """
    for cle, (modele, libelle) in types_de_fiches().items():
        if type_choisi and cle != type_choisi:
            continue
        # Les fiches Lore sont communes à tout l'univers (elles ne sont
        # rangées dans aucune campagne) : un filtre de campagne les écarte.
        if campagne and modele is LorePage:
            continue
        if campagne and modele is LieuPage:
            # Les lieux vivent dans l'encyclopédie, pas dans les campagnes :
            # un lieu appartient à une campagne s'il APPARAÎT sur une de ses
            # cartes. distinct() : un lieu présent sur 2 cartes ne compte qu'une fois.
            cartes = CartePage.objects.descendant_of(campagne)
            yield cle, modele.objects.live().filter(apparitions__carte__in=cartes).distinct()
            continue
        yield cle, modele.objects.live().descendant_of(campagne or accueil)


def etiqueter(requete, cle):
    """
    Exécute la requête et colle sur chaque fiche son type (clé + libellé) :
    le template s'en sert pour le badge et la couleur (data-type).
    """
    libelle = types_de_fiches()[cle][1]
    fiches = list(requete.prefetch_related('tags'))
    for fiche in fiches:
        fiche.type_cle = cle
        fiche.type_libelle = libelle
    return fiches


def fiches_liees(page, nombre=4, exclure=()):
    """
    Les fiches qui partagent au moins un tag avec `page`, de la plus proche
    (le plus de tags en commun) à la moins proche. Les épinglées passent
    devant à égalité. `exclure` : pk de fiches déjà affichées ailleurs sur la page.
    """
    tags = list(page.tags.all())
    if not tags:
        return []
    accueil = page.get_site().root_page
    fiches = []
    for cle, requete in requetes_de_fiches(accueil):
        # filter() AVANT annotate() : Count ne compte que les tags en commun
        requete = (requete.filter(tags__in=tags)
                   .exclude(pk=page.pk)
                   .exclude(pk__in=exclure)
                   .annotate(tags_communs=Count('tags')))
        fiches += etiqueter(requete, cle)
    fiches.sort(key=lambda fiche: (-fiche.tags_communs, not fiche.epinglee, fiche.title.lower()))
    return fiches[:nombre]
