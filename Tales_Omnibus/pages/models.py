from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.models import Page, Site
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.snippets.models import register_snippet

from core.blocks import BaseStreamBlock
from core.slugs import SlugAutomatiqueMixin


from encyclopedie.models import EncyclopedieIndexPage


# 1. MENTIONS LÉGALES : le texte légal est FIXE (dans le template), le client
#    ne remplit que ce qu'on ne peut pas deviner (qui édite, qui héberge).
#    Le reste s'insère tout seul : nom du site, adresse, page Contact, date.
class MentionsLegalesPage(SlugAutomatiqueMixin, Page):
    slug_fixe = "mentions-legales"  # = le lien du pied de page

    class Meta:
        verbose_name = "Mentions légales"
        verbose_name_plural = "Mentions légales"

    STATUTS = [
        ('particulier', "Particulier"),
        ('professionnel', "Professionnel (micro-entreprise, société…)"),
        ('association', "Association"),
    ]

    # --- Éditeur : la personne (ou structure) responsable du site ---
    editeur_nom = models.CharField(max_length=255, verbose_name="Nom ou raison sociale")
    editeur_statut = models.CharField(max_length=20, choices=STATUTS, default='particulier', verbose_name="Statut")
    editeur_adresse = models.TextField(
        blank=True, verbose_name="Adresse",
        help_text="Un particulier peut la laisser vide : elle doit alors être connue de l'hébergeur."
    )
    editeur_email = models.EmailField(verbose_name="Email de contact")
    siret = models.CharField(
        max_length=20, blank=True, verbose_name="SIRET / RNA",
        help_text="Obligatoire pour un professionnel (SIRET) ou une association (RNA)."
    )
    directeur_publication = models.CharField(
        max_length=255, blank=True, verbose_name="Directeur de la publication",
        help_text="Si vide, c'est l'éditeur."
    )

    # --- Hébergeur : obligatoire (loi pour la confiance dans l'économie numérique) ---
    hebergeur_nom = models.CharField(max_length=255, verbose_name="Nom de l'hébergeur")
    hebergeur_adresse = models.TextField(verbose_name="Adresse de l'hébergeur")
    hebergeur_contact = models.CharField(
        max_length=255, blank=True, verbose_name="Téléphone ou site de l'hébergeur"
    )

    # --- Parties libres ---
    credits = RichTextField(
        blank=True, features=['bold', 'italic', 'link', 'ul'],
        verbose_name="Crédits",
        help_text="Illustrations, cartes, polices, musiques… et leurs auteurs."
    )
    complement = RichTextField(
        blank=True, features=['h3', 'bold', 'italic', 'link', 'ul', 'ol'],
        verbose_name="Informations complémentaires",
        help_text="Ajouté à la fin, après les sections automatiques."
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('editeur_nom'),
            FieldPanel('editeur_statut'),
            FieldPanel('editeur_adresse'),
            FieldPanel('editeur_email'),
            FieldPanel('siret'),
            FieldPanel('directeur_publication'),
        ], heading="Éditeur du site"),
        MultiFieldPanel([
            FieldPanel('hebergeur_nom'),
            FieldPanel('hebergeur_adresse'),
            FieldPanel('hebergeur_contact'),
        ], heading="Hébergeur"),
        FieldPanel('credits'),
        FieldPanel('complement'),
    ]

    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1  # une seule page de mentions légales

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # Inserts automatiques : rien à retaper si le site change d'adresse
        # ou si la page Contact est renommée.
        accueil = Site.find_for_request(request).root_page.specific
        context['adresse_site'] = request.build_absolute_uri('/')
        context['page_contact'] = getattr(accueil, 'page_contact', None)
        # Le lecteur Twitch/YouTube de l'accueil dépose ses propres cookies :
        # on le signale seulement s'il est réellement affiché.
        noms = {'twitch': "Twitch", 'youtube': "YouTube"}
        lecteurs = getattr(accueil, 'stream_player', None) or []
        context['lecteur_live'] = next(
            (noms.get(bloc.value.get('plateforme'), "vidéo") for bloc in lecteurs), None
        )
        return context


# 1 bis. Page UNIVERS : le MJ d'un côté, le monde qu'il a construit de l'autre
class UniversPage(SlugAutomatiqueMixin, Page):
    slug_fixe = "univers"

    class Meta:
        verbose_name = "Univers"

    # --- Partie MJ (carte du haut + grande image, wireframe) ---
    mj_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Photo du MJ ou logo"
    )
    mj_presentation = RichTextField(
        blank=True,
        features=['bold', 'italic', 'link', 'ol', 'ul'],
        verbose_name="Présentation du MJ",
        help_text="Qui tu es, comment tu mènes tes parties..."
    )

    # --- Partie Univers (le monde) ---
    # "intro" garde ce nom : l'accueil la reprend quand son accroche est vide.
    intro = models.TextField(
        blank=True,
        verbose_name="Accroche de l'univers",
        help_text="Quelques phrases pour donner envie. Reprise sur l'accueil."
    )
    body = StreamField(
        BaseStreamBlock(), use_json_field=True, blank=True,
        verbose_name="Présentation du monde",
        help_text="Histoire, géographie, ambiance... (texte, images, vidéos)"
    )

    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1  # un seul univers par site

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('mj_image'),
            FieldPanel('mj_presentation'),
        ], heading="Le MJ"),
        MultiFieldPanel([
            FieldPanel('intro'),
            FieldPanel('body'),
        ], heading="L'univers"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # Le gros bouton "Explore mon univers" mène à l'encyclopédie
        context['encyclopedie'] = EncyclopedieIndexPage.objects.live().first()
        return context


# 2. Champs dynamiques du formulaire de contact
class ContactFormField(AbstractFormField):
    page = ParentalKey(
        'ContactPage',
        on_delete=models.CASCADE,
        related_name='form_fields'
    )


# 3. Modèle pour la page de contact
class ContactPage(SlugAutomatiqueMixin, AbstractEmailForm):
    slug_fixe = "contact"

    intro = RichTextField(blank=True, verbose_name="Texte de présentation")
    thank_you_text = RichTextField(blank=True, verbose_name="Message de confirmation")
    
    main_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Image d'illustration"
    )

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('main_image'),
        FieldPanel('intro'),
        InlinePanel('form_fields', label="Champs du formulaire"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldPanel('to_address', heading="Destinataire (Email)"),
            FieldPanel('from_address', heading="Expéditeur (Email)"),
            FieldPanel('subject', heading="Sujet du mail"),
        ], heading="Configuration de l'envoi d'e-mail"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['prestations'] = Prestation.objects.all()
        return context


# 4. PRESTATIONS : snippet (menu « Fragments » de l'admin).
#    Pas une page : une prestation n'a pas d'URL à elle, mais elle s'affiche
#    à deux endroits (page Contact + box Contact de l'accueil). Le client la
#    saisit une fois ; s'il n'en crée aucune, les sections ne s'affichent pas.
@register_snippet
class Prestation(models.Model):
    titre = models.CharField(max_length=100, verbose_name="Titre")
    description = RichTextField(
        blank=True,
        features=['bold', 'italic', 'link', 'ul'],
        verbose_name="Description"
    )
    prix = models.CharField(
        max_length=100, blank=True,
        verbose_name="Prix",
        help_text="Texte libre : « 30 € la séance », « Sur devis », « Gratuit »..."
    )
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="Les plus petits nombres s'affichent en premier."
    )

    panels = [
        FieldPanel('titre'),
        FieldPanel('description'),
        FieldPanel('prix'),
        FieldPanel('ordre'),
    ]

    class Meta:
        ordering = ['ordre', 'titre']
        verbose_name = "Prestation"
        verbose_name_plural = "Prestations"

    def __str__(self):
        return self.titre
