from django.contrib import messages
from django.core.mail import EmailMessage
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from modelcluster.fields import ParentalKey
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Orderable
from core.models import BaseFichePage, CategorieLieu, SOCIAL_PLATFORMS
from core.forms import HeroContactForm
from core.blocks import BaseStreamBlock
from core.panels import panels_avec_enfants
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

class CampagnesIndexPage(Page):
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
class CampagnePage(Page):
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

    subpage_types = ['campagnes.LieuPage']
    parent_page_types = ['campagnes.CampagnePage']

    content_panels = panels_avec_enfants(BaseFichePage.content_panels, "Lieux de cette carte", [
        FieldPanel('is_main_map'),
        FieldPanel('echelle_km'),
    ])

    def get_context(self, request):
        context = super().get_context(request)
        # Récupère automatiquement tous les lieux de CETTE carte
        # (LieuPage.objects -> pages "spécifiques" : on a accès à coord_x, coord_y, categorie)
        context['lieux'] = LieuPage.objects.child_of(self).live().select_related('categorie')

        parent_campagne = self.get_parent().specific
        autres_cartes = parent_campagne.get_children().live().type(CartePage).not_page(self)
        
        context['autres_cartes'] = autres_cartes
        return context

class LieuPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'LieuPage',
        on_delete=models.CASCADE,
        related_name='tagged_items'
    )

class LieuPage(BaseFichePage):
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
    # Coordonnées pour les markers sur la CartePage    
    coord_x = models.FloatField(
        null=True, blank=True,
        verbose_name="Coordonnée X (%)",
        help_text="Position horizontale sur la carte parent (de 0 à 100)"
    )
    coord_y = models.FloatField(
        null=True, blank=True,
        verbose_name="Coordonnée Y (%)",
        help_text="Position verticale sur la carte parent (de 0 à 100)"
    )
    subpage_types = []  # Page feuille (pas d'enfants)
    parent_page_types = ['campagnes.CartePage']
    tags = ClusterTaggableManager(through=LieuPageTag, blank=True)

    content_panels = BaseFichePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('categorie'),
            FieldPanel('coord_x'),
            FieldPanel('coord_y'),
        ], heading="Géolocalisation & Typologie"),
        FieldPanel("tags"),
    ]

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

class EvenementPage(BaseFichePage):
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

    subpage_types = []
    parent_page_types = ['campagnes.ChronologiePage']
    tags = ClusterTaggableManager(through=EvenementPageTag, blank=True)

    content_panels = BaseFichePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('date_ordre'),
            FieldPanel('date_affichage'),
        ], heading="Horodatage"),
        FieldPanel("tags"),
    ]

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

class HeroPage(BaseFichePage):
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
    
    tags = ClusterTaggableManager(through=HeroPageTag, blank=True)
    
    content_panels = BaseFichePage.content_panels + [
        MultiFieldPanel([
        FieldPanel('joueur_nom'),
        FieldPanel('joueur_email'),
        FieldPanel("joueur_bio"),
        FieldPanel('enable_contact'),
        InlinePanel('hero_social_links', label="Réseaux sociaux du joueur"),
        FieldPanel("tags"),
        ])]

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
