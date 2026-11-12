from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from modelcluster.fields import ParentalKey
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Orderable
from core.models import BaseFichePage, CategorieLieu, FicheEncyclopedieMixin, SOCIAL_PLATFORMS
from core.forms import HeroContactForm
from core.blocks import BaseStreamBlock
from core.panels import panels_avec_enfants
from core.slugs import SlugAutomatiqueMixin
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
        InlinePanel('apparitions', heading="Lieux sur cette carte", label="Lieu"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        # Les lieux posés sur CETTE carte (seulement les fiches publiées),
        # avec leur catégorie en une seule requête (couleur des étoiles).
        context['apparitions'] = (
            self.apparitions.filter(lieu__live=True)
            .select_related('lieu', 'lieu__categorie')
        )

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
    a_cette_epoque = models.TextField(
        blank=True,
        verbose_name="À cette époque",
        help_text="Ce qui est propre à cette carte : « caché par le brouillard », « en ruines »…"
    )

    panels = [
        FieldPanel('lieu'),
        FieldPanel('coord_x'),
        FieldPanel('coord_y'),
        FieldPanel('a_cette_epoque'),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Apparition d'un lieu"

    @property
    def est_placee(self):
        return self.coord_x is not None and self.coord_y is not None


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

    categorie = models.ForeignKey(
        CategorieLieu,  # <-- Utilisation directe
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='lieux',
        verbose_name="Catégorie de lieu"
    )
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

    subpage_types = []
    parent_page_types = ['campagnes.ChronologiePage']
    tags = ClusterTaggableManager(through=EvenementPageTag, blank=True)

    content_panels = BaseFichePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('date_ordre'),
            FieldPanel('date_affichage'),
        ], heading="Horodatage"),
        FieldPanel('lieu'),
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

    tags = ClusterTaggableManager(through=HeroPageTag, blank=True)
    
    content_panels = BaseFichePage.content_panels + [
        MultiFieldPanel([
        FieldPanel('joueur_nom'),
        FieldPanel('joueur_email'),
        FieldPanel("joueur_bio"),
        FieldPanel('enable_contact'),
        InlinePanel('hero_social_links', label="Réseaux sociaux du joueur"),
        FieldPanel("tags"),
        ]),
        FieldPanel("lieu_origine"),
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
