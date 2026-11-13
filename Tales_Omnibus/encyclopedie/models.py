from django import forms
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, Q
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import Tag, TaggedItemBase
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet

from campagnes.models import CampagnePage, CartePage, EvenementPage, HeroPage, LieuPage
from core.slugs import SlugAutomatiqueMixin
from core.models import (
    BaseFichePage, FicheEncyclopedieMixin, arbre_des_categories, categories_en_memoire, ids_de_la_branche,
)


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
        toutes_les_categories = categories_en_memoire()

        # --- 1. Les filtres choisis, lus dans l'URL (?campagne=3&categorie=7&tag=dragon)
        #     Formulaire en GET : l'URL filtrée peut être partagée ou mise en favori.
        #     Une valeur inconnue est simplement ignorée (pas d'erreur 500).
        id_campagne = request.GET.get('campagne', '')
        campagne = campagnes.filter(pk=id_campagne).first() if id_campagne.isdigit() else None
        id_categorie = request.GET.get('categorie', '')
        categorie = toutes_les_categories.get(int(id_categorie)) if id_categorie.isdigit() else None
        tag_choisi = request.GET.get('tag', '')
        # ?type=lieux reste accepté (liens existants), mais le visiteur filtre
        # désormais par CATÉGORIE : c'est son vocabulaire, pas celui de l'admin.
        type_choisi = request.GET.get('type') if request.GET.get('type') in types else ''

        # Choisir « Personnage » = la catégorie ET toute sa branche (Héros, PNJ, Déités…)
        branche = ids_de_la_branche(categorie, toutes_les_categories) if categorie else set()

        # --- 2. Pour chaque type de fiche, une requête avec les filtres
        fiches = []
        slugs_disponibles = set()
        for cle, requete in requetes_de_fiches(accueil, campagne, type_choisi):
            if categorie:
                condition = Q(categorie_id__in=branche)
                # Les fiches SANS catégorie sont dans la catégorie par défaut de
                # leur type : si celle-ci est dans la branche, elles en font partie.
                defaut = next((c for c in toutes_les_categories.values() if c.par_defaut_pour == cle), None)
                if defaut and defaut.pk in branche:
                    condition |= Q(categorie__isnull=True)
                requete = requete.filter(condition)

            # Les tags proposés = ceux des fiches AVANT le filtre de tag,
            # sinon il ne resterait que le tag cliqué et on ne pourrait plus en changer.
            slugs_disponibles.update(requete.filter(tags__isnull=False).values_list('tags__slug', flat=True))

            if tag_choisi:
                requete = requete.filter(tags__slug=tag_choisi)
            fiches += etiqueter(requete, cle, toutes_les_categories)

        # Les 4 types sont mélangés : un seul tri pour tout le monde,
        # les fiches épinglées d'abord, puis par ordre alphabétique.
        fiches.sort(key=lambda fiche: (not fiche.epinglee, fiche.title.lower()))

        # --- 3. Pagination : Django découpe la liste en pages de 12.
        #     get_page() est tolérant : ?page=abc ou ?page=999 donne une page valide.
        page_de_fiches = Paginator(fiches, self.FICHES_PAR_PAGE).get_page(request.GET.get('page'))

        context.update({
            'fiches': page_de_fiches,
            'campagnes': campagnes,
            # Le menu « Catégorie » : l'arbre à plat, indenté selon la profondeur
            'options_categories': [
                (c.pk, "\u00a0\u00a0\u00a0" * profondeur + c.nom)
                for c, profondeur in arbre_des_categories(toutes_les_categories)
            ],
            # Les pastilles, rangées par famille (snippet FamilleDeTags)
            'groupes_de_tags': ranger_par_famille(Tag.objects.filter(slug__in=slugs_disponibles)),
            'campagne_choisie': campagne,
            'categorie_choisie': categorie,
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
class LorePage(FicheEncyclopedieMixin, BaseFichePage):
    class Meta:
        verbose_name = "Fiche Lore"
        verbose_name_plural = "Fiches Lore"

    tags = ClusterTaggableManager(through=LorePageTag, blank=True)

    type_fiche = 'lore'
    subpage_types = []  # Page feuille
    parent_page_types = ['encyclopedie.EncyclopedieIndexPage']

    content_panels = BaseFichePage.content_panels + [
        FieldPanel('categorie'),
        FieldPanel('tags'),
        FieldPanel('epinglee'),
        InlinePanel('presences', heading="Dans les campagnes", label="Campagne"),
    ]


class PresenceEnCampagne(Orderable):
    """
    Une fiche Lore PRÉSENTE dans une campagne, avec ce qui lui est propre là :
    « Vaël, déesse des Brumes » dans « Les Brumes d'Ardenn » : « Vénérée en
    secret depuis le Grand Brouillard ».

    Même idée que les Apparitions des lieux : un lieu apparaît sur des CARTES,
    une fiche Lore apparaît dans des CAMPAGNES. Héros et événements n'en ont
    pas besoin : leur campagne, c'est la page au-dessus d'eux dans l'arbre.
    Sans aucune présence, la fiche reste universelle.
    """
    fiche = ParentalKey('LorePage', on_delete=models.CASCADE, related_name='presences')
    campagne = models.ForeignKey(
        'campagnes.CampagnePage',
        on_delete=models.CASCADE,  # campagne supprimée = présence supprimée
        related_name='+',
        verbose_name="Campagne",
    )
    texte = models.TextField(
        blank=True,
        verbose_name="Dans cette campagne",
        help_text="Ce que les joueurs de cette campagne en savent, ou ce qui y change."
    )

    panels = [
        FieldPanel('campagne'),
        FieldPanel('texte'),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Présence dans une campagne"


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
        if campagne and modele is LorePage:
            # Le Lore n'est rangé dans aucune campagne : il en fait partie
            # s'il y est déclaré PRÉSENT (modèle PresenceEnCampagne).
            yield cle, modele.objects.live().filter(presences__campagne=campagne).distinct()
            continue
        if campagne and modele is LieuPage:
            # Les lieux vivent dans l'encyclopédie, pas dans les campagnes :
            # un lieu appartient à une campagne s'il APPARAÎT sur une de ses
            # cartes. distinct() : un lieu présent sur 2 cartes ne compte qu'une fois.
            cartes = CartePage.objects.descendant_of(campagne)
            yield cle, modele.objects.live().filter(apparitions__carte__in=cartes).distinct()
            continue
        yield cle, modele.objects.live().descendant_of(campagne or accueil)


def etiqueter(requete, cle, toutes_les_categories=None):
    """
    Exécute la requête et colle sur chaque fiche :
      - son type (clé + libellé), pour la couleur par défaut (data-type) ;
      - sa catégorie affichée (la sienne ou celle par défaut de son type),
        avec ses parents déjà en mémoire : aucune requête de plus par fiche.
    """
    toutes = toutes_les_categories or categories_en_memoire()
    defaut = next((c for c in toutes.values() if c.par_defaut_pour == cle), None)
    libelle = types_de_fiches()[cle][1]
    fiches = list(requete.prefetch_related('tags'))
    for fiche in fiches:
        fiche.type_cle = cle
        fiche.type_libelle = libelle
        fiche.categorie_affichee = toutes.get(fiche.categorie_id) or defaut
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


# 5. FAMILLES DE TAGS : un snippet (menu Fragments) qui RANGE les tags existants.
#    C'est le tag qui a une famille, pas la page (≠ catégorie de lieu) : on
#    range « dragon » dans « Créatures » une fois, et toutes les fiches
#    taguées « dragon » en profitent. Les tags taggit ne sont pas modifiés.

class FamilleDeTagsForm(WagtailAdminModelForm):
    """Formulaire d'admin : un tag ne peut être rangé que dans UNE famille."""

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        autres_familles = FamilleDeTags.objects.exclude(pk=self.instance.pk)
        deja_ranges = tags.filter(familles__in=autres_familles).distinct()
        if deja_ranges:
            noms = ", ".join(tag.name for tag in deja_ranges)
            raise ValidationError(f"Déjà rangé dans une autre famille : {noms}.")
        return tags


@register_snippet
class FamilleDeTags(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom de la famille")
    icone = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Icône",
        help_text="Petite image carrée, affichée devant chaque tag de la famille."
    )
    couleur = models.CharField(
        max_length=7, default="#8C782C",
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', "Code couleur au format #RRGGBB.")],
        verbose_name="Couleur",
        help_text="Code HEX, ex : #3B6EA2. Utilisée si la famille n'a pas d'icône."
    )
    ordre = models.PositiveIntegerField(
        default=0, verbose_name="Ordre d'affichage",
        help_text="Les familles s'affichent de la plus petite valeur à la plus grande."
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name='familles',
        verbose_name="Tags de cette famille",
    )

    base_form_class = FamilleDeTagsForm
    panels = [
        FieldPanel('nom'),
        FieldPanel('icone'),
        FieldPanel('couleur'),
        FieldPanel('ordre'),
        # Cases à cocher : le MJ voit tous ses tags d'un coup d'œil
        FieldPanel('tags', widget=forms.CheckboxSelectMultiple),
    ]

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Famille de tags"
        verbose_name_plural = "Familles de tags"

    def __str__(self):
        return self.nom


def ranger_par_famille(tags):
    """
    Range des tags (objets Tag) par famille, dans l'ordre des familles, puis
    les tags sans famille dans un dernier groupe « Autres ».
    Renvoie [{'famille': FamilleDeTags ou None, 'tags': [Tag, …]}, …] et
    colle sur chaque tag sa famille (tag.famille) pour l'icône et la couleur.
    2 requêtes en tout, quel que soit le nombre de tags.
    """
    familles = list(FamilleDeTags.objects.select_related('icone').prefetch_related('tags'))
    famille_du_tag = {tag.pk: famille for famille in familles for tag in famille.tags.all()}

    groupes = {famille.pk: [] for famille in familles}
    autres = []
    for tag in sorted(tags, key=lambda tag: tag.name.lower()):
        tag.famille = famille_du_tag.get(tag.pk)
        (groupes[tag.famille.pk] if tag.famille else autres).append(tag)

    resultat = [{'famille': f, 'tags': groupes[f.pk]} for f in familles if groupes[f.pk]]
    if autres:
        resultat.append({'famille': None, 'tags': autres})
    return resultat


def campagnes_de(fiche):
    """
    Les campagnes (publiées) d'une fiche, quel que soit son type :
      - Héros, Événement : la campagne au-dessus d'eux dans l'arbre des pages ;
      - Lieu : les campagnes des cartes où il apparaît (modèle Apparition) ;
      - Lore : les campagnes où il est déclaré présent (PresenceEnCampagne).
    Renvoie [(campagne, texte propre à cette campagne ou ""), …].
    """
    campagnes = CampagnePage.objects.live()
    if isinstance(fiche, LorePage):
        presences = fiche.presences.filter(campagne__live=True).select_related('campagne')
        return [(p.campagne, p.texte) for p in presences]
    if isinstance(fiche, LieuPage):
        # Arbre Wagtail : le chemin du parent = le chemin de la carte sans son
        # dernier segment de 4 caractères (même astuce que la migration 0014).
        chemins = {a.carte.path[:-4] for a in fiche.apparitions.select_related('carte')}
        return [(c, "") for c in campagnes.filter(path__in=chemins).order_by('path')]
    return [(c, "") for c in campagnes.ancestor_of(fiche)]
