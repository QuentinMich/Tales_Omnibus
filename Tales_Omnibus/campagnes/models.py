from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from modelcluster.fields import ParentalKey
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Orderable
from wagtail.search import index
from core.models import (
    BaseFichePage, FicheEncyclopedieMixin, SOCIAL_PLATFORMS, arbre_des_categories, categories_en_memoire,
)
from core.forms import HeroContactForm
from core.blocks import STATS_DND, BaseStreamBlock, TableauDeStatsBlock
from core.panels import panels_avec_enfants
from core.slugs import SlugAutomatiqueMixin
from .geometrie import aire, centre, contient, est_une_forme_valide, ranger
from .panels import EditeurDeCartePanel
from .widgets import OutilsDeCarteWidget
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

class CampagnesIndexPage(SlugAutomatiqueMixin, Page):
    slug_fixe = "campagnes"  # = le lien « Campagnes » du menu

    class Meta:
        verbose_name = "Index des campagnes"
        verbose_name_plural = "Index des campagnes"

    intro = RichTextField(
        blank=True, 
        features=['bold', 'italic', 'link'], 
        verbose_name="Présentation des campagnes"
    )

    # Restriction : Dans l'Index, on ne peut créer QUE des CampagnePage
    subpage_types = ['campagnes.CampagnePage']
    parent_page_types = ['home.HomePage']

    content_panels = panels_avec_enfants(Page.content_panels, "Campagnes", [
        FieldPanel('intro'),
    ])

    def get_context(self, request):
        context = super().get_context(request)
        # 1. On récupère toutes les campagnes publiées (sans limite max)
        campagnes_list = list(self.get_children().live().type(CampagnePage))
        
        # 2. Gestion du minimum de 3 cartes pour l'affichage visuel
        count = len(campagnes_list)
        placeholders = range(3 - count) if count < 3 else []
        
        context['campagnes'] = campagnes_list
        context['placeholders'] = placeholders
        return context

# 1. CAMPAGNE (Conteneur principal de la saison)
class CampagnePage(SlugAutomatiqueMixin, Page):
    class Meta:
        verbose_name = "Campagne"
        verbose_name_plural = "Campagnes"

# Choix des statuts
    STATUS_CHOICES = [
        ('en_cours', 'En cours'),
        ('a_venir', 'À venir'),
        ('termine', 'Terminé'),
    ] 
# En-tête & Carte d'index
    subtitle = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Sous-titre / Saison",
        help_text="Ex: Saison 1 - Les Terres d'Aethelgard"
    )
    card_description = models.CharField(
        max_length=300, 
        blank=True, 
        verbose_name="Courte description (pour les cartes)",
        help_text="Un petit texte d'accroche utilisé sur la page d'accueil et l'index des campagnes."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='en_cours',
        verbose_name="Statut de la campagne"
    )
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Image de couverture / Bannière"
    )

    # Contenu détaillé de la campagne
    synopsis = RichTextField(
        blank=True, 
        features=['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul', 'blockquote'], 
        verbose_name="Synopsis complet"
    )
    body = StreamField(BaseStreamBlock(), use_json_field=True, blank=True, verbose_name="Contenu libre")

    # Dans une Campagne, on ne peut créer QUE des Cartes, Chronologies ou Héros
    subpage_types = [
        'campagnes.CartePage',
        'campagnes.ChronologiePage',
        'campagnes.HeroPage',
    ]
    parent_page_types = ['campagnes.CampagnesIndexPage']

    # Recherche : la campagne est retrouvée par son sous-titre, son accroche,
    # son synopsis et son contenu (pas seulement par son titre)
    search_fields = Page.search_fields + [
        index.SearchField('subtitle'),
        index.SearchField('card_description'),
        index.SearchField('synopsis'),
        index.SearchField('body'),
    ]

    content_panels = panels_avec_enfants(Page.content_panels, "Cartes, chronologie et héros", [
        MultiFieldPanel([
            FieldPanel('subtitle'),
            FieldPanel('banner_image'),
            FieldPanel('status'),
            FieldPanel('card_description'),
        ], heading="Présentation & VIGNETTE"),
        FieldPanel('synopsis'),
        FieldPanel('body'),
    ])
    def get_context(self, request):
        context = super().get_context(request)
        cartes_qs = [c.specific for c in self.get_children().live().type(CartePage)]
        carte_principale = None

        if cartes_qs:
            # Cherche la carte cochée is_main_map=True, sinon prend la première par défaut
            principales = [c for c in cartes_qs if getattr(c, 'is_main_map', False)]
            carte_principale = principales[0] if principales else cartes_qs[0]


        context['carte_principale'] = carte_principale

        chronologie = ChronologiePage.objects.child_of(self).live().first()
        context['chronologie'] = chronologie
        # Bloc "Événements récents" du wireframe : les 4 derniers dans l'ordre de l'histoire
        context['evenements_recents'] = (
            EvenementPage.objects.child_of(chronologie).live().order_by('-date_ordre')[:4]
            if chronologie else []
        )

        context['heros'] = HeroPage.objects.child_of(self).live()
        return context

# 2. CARTE (Conteneur de lieux)
class CartePage(BaseFichePage):
    class Meta:
        verbose_name = "Carte"
        verbose_name_plural = "Cartes"

    is_main_map = models.BooleanField(
        default=False,
        verbose_name="Carte principale de la campagne",
        help_text="Cochez pour afficher cette carte en vedette sur la page de la campagne."
    )
    echelle_km = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Échelle (en km par carreau/grille)",
        help_text="Optionnel : pour donner l'échelle du territoire."
    )

    # Les lieux ne sont plus rangés SOUS la carte : ce sont des fiches de
    # l'encyclopédie, posées sur une ou plusieurs cartes par des Apparitions.
    subpage_types = []
    parent_page_types = ['campagnes.CampagnePage']

    content_panels = BaseFichePage.content_panels + [
        FieldPanel('is_main_map'),
        FieldPanel('echelle_km'),
        # L'image de la carte, cliquable : sert aux boutons « Placer » / « Tracer »
        # de chaque lieu ci-dessous (voir campagnes/static/campagnes/js/editeur_carte.js)
        EditeurDeCartePanel(heading="Placer les lieux sur la carte"),
        InlinePanel('apparitions', heading="Lieux sur cette carte", label="Lieu"),
    ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # update_fields rempli = Wagtail n'enregistre que quelques champs
        # (ex. un brouillon) : les apparitions en base ne bougent pas, on ne
        # recalcule rien. Sinon (publication) : on refait l'arbre de la carte.
        if kwargs.get('update_fields') is None:
            self.ranger_les_lieux()

    def ranger_les_lieux(self, enregistrer=True):
        """
        « Qui est dans qui » sur CETTE carte (règles dans geometrie.ranger) :
        remplit Apparition.contenu_dans. Pour une zone, l'étoile (coord_x /
        coord_y) est replacée au centre de la zone.
        Appelé à chaque publication de la carte : l'arbre est toujours à jour.

        Renvoie le nombre de lieux dont la position ou le parent a changé.
        enregistrer=False : calcule sans rien écrire (simulation de
        manage.py entretien).
        """
        apparitions = list(self.apparitions.all())
        avant = {a.pk: (a.coord_x, a.coord_y, a.contenu_dans_id) for a in apparitions}
        for apparition in apparitions:
            # Centre placé à la main (forme en croissant, en L…) : on le garde
            if apparition.est_zone and not (apparition.centre_manuel and apparition.est_placee):
                x, y = centre(apparition.forme)
                apparition.coord_x, apparition.coord_y = round(x, 2), round(y, 2)

        parents = ranger([
            {
                'cle': index,
                'lieu': apparition.lieu_id,
                'point': (apparition.coord_x, apparition.coord_y) if apparition.est_placee else None,
                'zone': apparition.forme if apparition.est_zone else None,
            }
            for index, apparition in enumerate(apparitions)
        ])
        changements = 0
        for index, apparition in enumerate(apparitions):
            parent = parents[index]
            apparition.contenu_dans_id = apparitions[parent].lieu_id if parent is not None else None
            if avant.get(apparition.pk) != (apparition.coord_x, apparition.coord_y, apparition.contenu_dans_id):
                changements += 1
            if apparition.pk and enregistrer:
                # update() : écrit directement en base, sans repasser par save()
                Apparition.objects.filter(pk=apparition.pk).update(
                    coord_x=apparition.coord_x, coord_y=apparition.coord_y,
                    contenu_dans_id=apparition.contenu_dans_id,
                )
        return changements

    def get_context(self, request):
        context = super().get_context(request)
        # Les lieux posés sur CETTE carte (seulement les fiches publiées),
        # avec leur catégorie en une seule requête (couleur des étoiles).
        apparitions = list(
            self.apparitions.filter(lieu__live=True)
            .select_related('lieu', 'lieu__categorie', 'lieu__categorie__parent')
        )
        # La catégorie de chaque lieu (pour sa couleur et son icône), avec
        # tout l'arbre chargé en UNE requête : remonter aux parents pour
        # hériter de l'icône ne coûte alors plus rien.
        toutes = categories_en_memoire()
        defaut = next((c for c in toutes.values() if c.par_defaut_pour == LieuPage.type_fiche), None)
        presentes = set()  # les catégories présentes sur la carte, avec leurs ancêtres
        for apparition in apparitions:
            categorie = toutes.get(apparition.lieu.categorie_id) or defaut
            apparition.categorie_affichee = categorie
            ancetres = categorie.ancetres() if categorie else []
            presentes.update(c.pk for c in ancetres)
            # Pour le filtre « Afficher » : « 8 10 11 » = Lieu, Village, Hameau.
            # Le JS montre l'élément si la catégorie choisie est DANS cette
            # liste : choisir « Village » montre donc aussi les hameaux.
            apparition.ids_categories = " ".join(str(c.pk) for c in ancetres)
        context['apparitions'] = apparitions
        # Le menu « Afficher » : l'arbre des catégories, réduit à celles
        # qui ont au moins un lieu sur CETTE carte (inutile de proposer
        # « Déité » sur une carte de villages).
        context['options_categories'] = [
            (c.pk, "\u00a0\u00a0\u00a0" * profondeur + c.nom)
            for c, profondeur in arbre_des_categories(toutes) if c.pk in presentes
        ]
        # Les zones, des plus grandes aux plus petites : en SVG, ce qui est
        # dessiné en dernier passe AU-DESSUS. La ville reste cliquable sur le royaume.
        context['zones'] = sorted((a for a in apparitions if a.est_zone), key=lambda a: -a.aire)

        parent_campagne = self.get_parent().specific
        autres_cartes = parent_campagne.get_children().live().type(CartePage).not_page(self)
        
        context['autres_cartes'] = autres_cartes
        return context

class Apparition(Orderable):
    """
    Un lieu POSÉ sur une carte : "Caer Fiodh, sur la carte Royaume, en x=12 y=20".

    Le même lieu peut apparaître sur plusieurs cartes (carte régionale et
    carte du monde, ou deux campagnes à des siècles d'écart) avec des
    coordonnées et un état différents. La fiche du lieu, elle, reste unique.
    ParentalKey : les apparitions s'éditent DANS la page Carte (InlinePanel)
    et sont publiées avec elle.
    """
    carte = ParentalKey('CartePage', on_delete=models.CASCADE, related_name='apparitions')
    lieu = models.ForeignKey(
        'campagnes.LieuPage',
        on_delete=models.CASCADE,  # fiche supprimée = plus d'étoile sur les cartes
        related_name='apparitions',  # lieu.apparitions = toutes les cartes où il figure
        verbose_name="Lieu",
    )
    # Vides = lieu ajouté à la carte mais pas encore placé (pas d'étoile)
    coord_x = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Coordonnée X (%)",
        help_text="Position horizontale sur cette carte (de 0 à 100)"
    )
    coord_y = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Coordonnée Y (%)",
        help_text="Position verticale sur cette carte (de 0 à 100)"
    )
    # Une ZONE (royaume, forêt…) : la liste des sommets du polygone, en %.
    # Vide = le lieu est un simple point (coord_x / coord_y).
    forme = models.JSONField(
        null=True, blank=True,
        verbose_name="Position sur la carte",
        help_text="Un point (une ville) ou une zone (un royaume) : utilise les boutons.",
    )
    # Pour une zone, l'étoile (coord_x / coord_y) est son centre, calculé tout
    # seul. Mais le centre d'une forme en croissant ou en L tombe parfois en
    # DEHORS de la forme : on peut alors le placer soi-même (bouton
    # « Placer le centre »), et cette case dit au calcul de ne pas l'écraser.
    centre_manuel = models.BooleanField(
        default=False,
        verbose_name="Centre placé à la main",
        help_text="Décoche pour revenir au centre calculé automatiquement.",
    )
    # Une zone pleine (un royaume) ou hachurée (no man's land, zone interdite…)
    MOTIFS = [
        ('plein', "Pleine"),
        ('hachures', "Hachurée"),
    ]
    motif = models.CharField(
        max_length=20, choices=MOTIFS, default='plein',
        verbose_name="Remplissage de la zone",
        help_text="Hachurée : pour un no man's land, une zone interdite… (sans effet sur un point)",
    )
    # Le trait du contour : une frontière nette, ou en tirets (frontière
    # floue, contestée, territoire revendiqué…). Indépendant du remplissage.
    BORDURES = [
        ('continue', "Trait continu"),
        ('tirets', "Tirets"),
    ]
    bordure = models.CharField(
        max_length=20, choices=BORDURES, default='continue',
        verbose_name="Frontière de la zone",
        help_text="Tirets : frontière floue ou contestée (sans effet sur un point)",
    )
    # CALCULÉ, jamais saisi : la plus petite zone de cette carte qui contient
    # ce lieu (voir CartePage.ranger_les_lieux). C'est la « géographie » :
    # Port-Lanterne est dans le Val Gris, lui-même dans Ardenn.
    # On pointe vers le LIEU (une page, stable) et pas vers son Apparition,
    # que Wagtail recrée quand on publie une ancienne révision.
    contenu_dans = models.ForeignKey(
        'campagnes.LieuPage',
        null=True, blank=True, editable=False,
        on_delete=models.SET_NULL,
        related_name='contenus',  # lieu.contenus = apparitions situées dans ce lieu
        verbose_name="Situé dans",
    )
    a_cette_epoque = models.TextField(
        blank=True,
        verbose_name="À cette époque",
        help_text="Ce qui est propre à cette carte : « caché par le brouillard », « en ruines »…"
    )

    panels = [
        FieldPanel('lieu'),
        FieldPanel('forme', widget=OutilsDeCarteWidget),
        FieldPanel('motif'),
        FieldPanel('bordure'),
        FieldPanel('coord_x'),
        FieldPanel('coord_y'),
        FieldPanel('centre_manuel'),
        FieldPanel('a_cette_epoque'),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Apparition d'un lieu"

    def clean(self):
        super().clean()
        if self.forme in ([], ""):
            self.forme = None
        if self.forme is not None and not est_une_forme_valide(self.forme):
            raise ValidationError({'forme': "Une zone a besoin d'au moins 3 points, entre 0 et 100."})
        # Le centre sert aussi à savoir dans quelle zone ELLE est rangée :
        # posé hors de la forme, il rangerait la zone n'importe où.
        if (self.centre_manuel and self.est_zone and self.est_placee
                and not contient(self.forme, self.coord_x, self.coord_y)):
            raise ValidationError({'coord_x': "Le centre placé à la main doit être à l'intérieur de la zone."})

    @property
    def est_placee(self):
        return self.coord_x is not None and self.coord_y is not None

    @property
    def est_zone(self):
        return bool(self.forme) and len(self.forme) >= 3

    @property
    def aire(self):
        return aire(self.forme) if self.est_zone else 0

    @property
    def points_svg(self):
        """
        L'attribut points d'un <polygon> SVG : « 10,20 40,25 30,60 ».
        Fabriqué en Python (et pas avec |unlocalize dans le template) :
        str() d'un nombre écrit toujours 12.5, jamais 12,5.
        """
        return " ".join(f"{x},{y}" for x, y in self.forme) if self.est_zone else ""

    @property
    def clip_path(self):
        """
        La même zone en CSS : « polygon(10% 20%, 40% 25%, …) ». Sert aux
        hachures, dessinées en CSS (un dégradé répété) puis découpées à la
        forme de la zone. En SVG étiré, les hachures seraient déformées ;
        en CSS, elles restent droites à 45°.
        """
        return "polygon(" + ", ".join(f"{x}% {y}%" for x, y in self.forme) + ")" if self.est_zone else ""

    @property
    def est_hachuree(self):
        return self.est_zone and self.motif == 'hachures'

    @property
    def classes_zone(self):
        """Les classes CSS du polygone : « carte-zone carte-zone--hachuree carte-zone--tirets »."""
        classes = ["carte-zone"]
        if self.est_hachuree:
            classes.append("carte-zone--hachuree")
        if self.bordure == 'tirets':
            classes.append("carte-zone--tirets")
        return " ".join(classes)

    # Mini-carte zoomée : la « boîte » à cadrer autour d'un POINT, en % de la
    # largeur de la carte (une zone, elle, donne sa propre boîte).
    VUE_AUTOUR_D_UN_POINT = 25

    @property
    def style_cadrage(self):
        """
        Les données du zoom de la mini-carte, en variables CSS :
        « --cx: 66; --cy: 24; --zw: 30; --zh: 30; --ratio: 1.5 ».
          - cx / cy : le centre à viser (le point, ou le milieu de la zone) ;
          - zw / zh : la taille de la boîte à faire tenir dans le cadre ;
          - ratio : hauteur / largeur de l'image de la carte.
        C'est structure.css qui en déduit le zoom et le décalage : Python
        donne les MESURES, le CSS fait la mise en page.
        Fabriqué en Python : str() écrit 12.5, jamais 12,5 (CSS valide).
        """
        image = self.carte.main_image
        if not image or not image.width or not self.est_placee:
            return ""
        ratio = image.height / image.width
        if self.est_zone:
            xs = [x for x, _ in self.forme]
            ys = [y for _, y in self.forme]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            # Une zone toute plate ferait un zoom infini : 5 % minimum
            zw, zh = max(5, max(xs) - min(xs)), max(5, max(ys) - min(ys))
        else:
            cx, cy = self.coord_x, self.coord_y
            # Une boîte CARRÉE sur l'image : en % de la hauteur, la même
            # longueur vaut moins sur une carte en portrait (÷ ratio).
            zw = self.VUE_AUTOUR_D_UN_POINT
            zh = zw / ratio
        return f"--cx: {round(cx, 2)}; --cy: {round(cy, 2)}; --zw: {round(zw, 2)}; --zh: {round(zh, 2)}; --ratio: {round(ratio, 4)};"

    @property
    def categorie_affichee(self):
        """
        La catégorie du lieu (couleur, icône sur la carte). La page Carte la
        pré-remplit pour tous ses lieux en une requête (voir get_context) ;
        ailleurs (mini-cartes), on la calcule ici.
        """
        if not hasattr(self, '_categorie_affichee'):
            self._categorie_affichee = self.lieu.categorie_effective
        return self._categorie_affichee

    @categorie_affichee.setter
    def categorie_affichee(self, valeur):
        self._categorie_affichee = valeur

    def chemin(self):
        """
        La géographie de ce lieu SUR CETTE CARTE, du plus grand au plus
        proche : [Ardenn, Royaume du Val Gris]. On remonte de zone en zone.
        """
        chemin, vus, courant = [], {self.lieu_id}, self
        while courant.contenu_dans_id and courant.contenu_dans_id not in vus:
            vus.add(courant.contenu_dans_id)
            chemin.insert(0, courant.contenu_dans)
            courant = (Apparition.objects.filter(carte_id=self.carte_id, lieu_id=courant.contenu_dans_id)
                       .select_related('contenu_dans').first())
            if courant is None:
                break
        return [lieu for lieu in chemin if lieu.live]


class LieuPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'LieuPage',
        on_delete=models.CASCADE,
        related_name='tagged_items'
    )

class LieuPage(FicheEncyclopedieMixin, BaseFichePage):
    class Meta:
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"

    # Le champ « categorie » vient de FicheEncyclopedieMixin (arbre des catégories)
    type_fiche = 'lieux'
    # Un lieu est une fiche UNIVERSELLE (comme le Lore) : il vit dans
    # l'encyclopédie. Ses positions sont dans les Apparitions des cartes.
    subpage_types = []  # Page feuille (pas d'enfants)
    parent_page_types = ['encyclopedie.EncyclopedieIndexPage']
    tags = ClusterTaggableManager(through=LieuPageTag, blank=True)

    content_panels = BaseFichePage.content_panels + [
        FieldPanel('categorie'),
        FieldPanel("tags"),
        FieldPanel("epinglee"),
    ]

    def apparitions_publiees(self):
        """Les cartes publiées où figure ce lieu, dans l'ordre de l'arborescence."""
        return (self.apparitions.filter(carte__live=True)
                .select_related('carte', 'lieu__categorie')
                .order_by('carte__path'))

    def lieux_contenus(self):
        """Les lieux situés DANS celui-ci, sur au moins une carte publiée."""
        return (LieuPage.objects.live()
                .filter(apparitions__contenu_dans=self, apparitions__carte__live=True)
                .distinct().order_by('title'))

    def apparition_vue_depuis(self, page):
        """
        La carte à montrer sur la fiche d'un héros ou d'un événement : de
        préférence une carte de LEUR campagne (le lieu tel qu'on le voyait à
        cette époque), sinon la première carte où le lieu figure.
        """
        apparitions = self.apparitions_publiees()
        campagne = CampagnePage.objects.ancestor_of(page).first()
        if campagne:
            dans_la_campagne = apparitions.filter(carte__in=CartePage.objects.descendant_of(campagne))
            if dans_la_campagne:
                return dans_la_campagne.first()
        return apparitions.first()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['apparitions'] = self.apparitions_publiees()
        context['lieux_contenus'] = self.lieux_contenus()
        return context

# 4. CHRONOLOGIE (Conteneur d'événements)
class ChronologiePage(BaseFichePage):
    class Meta:
        verbose_name = "Chronologie"
        verbose_name_plural = "Chronologies"

    systeme_datation = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Système de datation",
        help_text="Ex: Calendrier Solaire, An 400 AP. J.C, etc."
    )

    subpage_types = ['campagnes.EvenementPage']
    parent_page_types = ['campagnes.CampagnePage']

    content_panels = panels_avec_enfants(BaseFichePage.content_panels, "Événements", [
        FieldPanel('systeme_datation'),
    ])

    def get_context(self, request):
        context = super().get_context(request)
        # On trie automatiquement les événements enfants par leur champ date_ordre
        context['evenements'] = (
            EvenementPage.objects.child_of(self).live().order_by('date_ordre')
        )
        return context

class EvenementPageTag(TaggedItemBase):
    content_object = ParentalKey('EvenementPage', on_delete=models.CASCADE, related_name='tagged_items')

class EvenementPage(FicheEncyclopedieMixin, BaseFichePage):
    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"

    date_ordre = models.IntegerField(
        default=0,
        verbose_name="Valeur numérique de date (pour le tri)",
        help_text="Permet de trier chronologiquement (ex: -50 pour 50 av. J-C, 1492, 10500...)"
    )
    date_affichage = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Date affichée",
        help_text="Ex: '14ème jour du Mois des Moissons, An 402'"
    )

    # Le "pin" de l'événement : on pointe vers un Lieu existant au lieu de
    # retaper des coordonnées. Si le lieu bouge sur la carte, l'événement suit.
    lieu = models.ForeignKey(
        'campagnes.LieuPage',
        null=True, blank=True,
        on_delete=models.SET_NULL,  # supprimer le lieu ne supprime pas l'événement
        related_name='evenements',  # lieu.evenements = ce qui s'est passé ici
        verbose_name="Lieu de l'événement",
        help_text="Un champ de bataille, une clairière… crée-le d'abord comme Lieu sur une carte."
    )

    type_fiche = 'evenements'
    subpage_types = []
    parent_page_types = ['campagnes.ChronologiePage']
    tags = ClusterTaggableManager(through=EvenementPageTag, blank=True)

    content_panels = BaseFichePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('date_ordre'),
            FieldPanel('date_affichage'),
        ], heading="Horodatage"),
        FieldPanel('lieu'),
        FieldPanel('categorie'),
        FieldPanel("tags"),
        FieldPanel("epinglee"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # Le "pin" : le lieu vu depuis une carte de la campagne de l'événement
        if self.lieu and self.lieu.live:
            context['apparition_lieu'] = self.lieu.apparition_vue_depuis(self)
        return context

class HeroSocialLink(Orderable):
    page = ParentalKey(
        'HeroPage', 
        related_name='hero_social_links', 
        on_delete=models.CASCADE
    )
    platform = models.CharField(
        max_length=50, 
        choices=SOCIAL_PLATFORMS,
        verbose_name="Plateforme"
    )
    url = models.URLField(verbose_name="Lien du profil joueur")

    panels = [
        FieldPanel('platform'),
        FieldPanel('url'),
    ]

class HeroPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'HeroPage',
        on_delete=models.CASCADE,
        related_name='tagged_items'
    )

class HeroPage(FicheEncyclopedieMixin, BaseFichePage):
    class Meta:
        verbose_name = "Héros"
        verbose_name_plural = "Héros"

    type_fiche = 'heros'
    subpage_types = []  # Page feuille
    parent_page_types = ['campagnes.CampagnePage']
    joueur_nom = models.CharField(max_length=100, verbose_name="Nom / Pseudo du joueur")
    joueur_bio = RichTextField(blank=True, verbose_name="Présentation du joueur", features=['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul', 'blockquote'])
    joueur_email = models.EmailField(blank=True, verbose_name="Email du joueur (réception des messages)")                           
    
    
    enable_contact = models.BooleanField(
        default=False, 
        verbose_name="Activer le formulaire de contact sur la fiche"
    )
    
    lieu_origine = models.ForeignKey(
        'campagnes.LieuPage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='heros_originaires',  # lieu.heros_originaires = qui vient d'ici
        verbose_name="Lieu d'origine",
    )

    # La fiche de stats : un ou plusieurs tableaux (Warhammer : profil +
    # compétences…). Un NOUVEAU héros arrive avec le tableau D&D prérempli ;
    # vide (on supprime le tableau) = rien sur le site.
    caracteristiques = StreamField(
        [('tableau', TableauDeStatsBlock())],
        blank=True,
        default=[('tableau', {
            'titre': "Caractéristiques", 'colonnes': 6, 'taille': 'grande',
            'stats': [{'libelle': nom, 'valeur': "", 'complement': ""} for nom in STATS_DND],
        })],
        verbose_name="Caractéristiques",
        help_text="Le modèle D&D est prérempli : renomme, ajoute ou retire des cases, "
                  "change le nombre de colonnes. Supprime le tableau pour ne rien afficher.",
    )

    tags = ClusterTaggableManager(through=HeroPageTag, blank=True)
    
    content_panels = BaseFichePage.content_panels + [
        # Entre la description du personnage et celle du joueur, comme sur la page
        FieldPanel('caracteristiques'),
        MultiFieldPanel([
        FieldPanel('joueur_nom'),
        FieldPanel('joueur_email'),
        FieldPanel("joueur_bio"),
        FieldPanel('enable_contact'),
        InlinePanel('hero_social_links', label="Réseaux sociaux du joueur"),
        FieldPanel("tags"),
        ]),
        FieldPanel("lieu_origine"),
        FieldPanel("categorie"),
        FieldPanel("epinglee"),
    ]

    @property
    def contact_actif(self):
        """Le formulaire n'a de sens que si on sait à qui envoyer le message."""
        return self.enable_contact and bool(self.joueur_email)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # Transmet l'instance du formulaire au template HTML de la fiche
        # (sauf si serve() en a déjà mis un, avec les erreurs de saisie)
        if self.contact_actif and 'contact_form' not in context:
            context['contact_form'] = HeroContactForm()
        # Le "pin" : le lieu d'origine vu depuis une carte de la campagne du héros
        if self.lieu_origine and self.lieu_origine.live:
            context['apparition_lieu'] = self.lieu_origine.apparition_vue_depuis(self)
        return context

    def serve(self, request, *args, **kwargs):
        if self.contact_actif and request.method == 'POST':
            form = HeroContactForm(request.POST)
            if form.is_valid():
                self.envoyer_message(form.cleaned_data)
                messages.success(request, "Votre message a bien été envoyé au joueur !")
                # Redirection après POST : évite le double envoi si on rafraîchit la page
                return redirect(self.get_url(request))

            # Formulaire invalide : on réaffiche la page avec les erreurs
            context = self.get_context(request, *args, **kwargs)
            context['contact_form'] = form
            return TemplateResponse(request, self.get_template(request), context)

        return super().serve(request, *args, **kwargs)

    def envoyer_message(self, data):
        raison = dict(HeroContactForm.base_fields['raison'].choices).get(data['raison'], data['raison'])
        EmailMessage(
            subject=f"[{self.title}] {raison} - de {data['nom']}",
            body=(
                f"Message reçu depuis la fiche de {self.title}.\n\n"
                f"Nom : {data['nom']}\n"
                f"Email : {data['email']}\n"
                f"Raison : {raison}\n\n"
                f"{data['message']}"
            ),
            to=[self.joueur_email],
            reply_to=[data['email']],  # le joueur peut répondre directement au visiteur
        ).send()
