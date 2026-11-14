from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import PageChooserBlock
from wagtail.fields import StreamField
from wagtail.models import Page

from campagnes.models import CampagnePage
from core.blocks import StreamPlayerBlock
from pages.models import Prestation, UniversPage


class HomePage(Page):
    class Meta:
        verbose_name = "Accueil"

    # 1. IMAGE D'OUVERTURE : plein écran, au-dessus du header (wireframe Accueil-1)
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Image d'ouverture",
        help_text="Grande image affichée en plein écran tout en haut de l'accueil."
    )

    # 2. LIVE : un seul lecteur Twitch ou YouTube (max_num=1)
    stream_player = StreamField(
        [('lecteur', StreamPlayerBlock())],
        use_json_field=True, blank=True, max_num=1,
        verbose_name="Lecteur de live"
    )

    # 3. UNIVERS : la page Univers est retrouvée par son type (une seule par
    #    site), on ne garde ici que l'accroche personnalisable de l'accueil.
    univers_accroche = models.TextField(
        blank=True,
        verbose_name="Accroche de l'univers",
        help_text="Courte présentation. Si vide, on reprend l'introduction de la page Univers."
    )

    # 4. ENCYCLOPÉDIE : 3 fiches Lore choisies à la main par le client
    encyclopedie_a_la_une = StreamField(
        [('fiche_lore', PageChooserBlock(page_type='encyclopedie.LorePage', label="Fiche Lore"))],
        use_json_field=True, blank=True, max_num=3,
        verbose_name="Fiches de l'encyclopédie à la une"
    )

    # 5. CONTACT : lien vers la page Contact (son intro est reprise sur l'accueil)
    page_contact = models.ForeignKey(
        'pages.ContactPage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Page Contact"
    )

    content_panels = Page.content_panels + [
        FieldPanel('hero_image'),
        FieldPanel('stream_player'),
        FieldPanel('univers_accroche'),
        FieldPanel('encyclopedie_a_la_une'),
        FieldPanel('page_contact'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # Les campagnes ne sont pas des enfants directs de l'accueil
        # (Accueil > Index des campagnes > Campagne) : on prend donc les
        # DESCENDANTS publiés, et seulement les 3 premières (wireframe).
        context['campagnes'] = CampagnePage.objects.live().descendant_of(self)[:3]
        # Une seule page Univers par site (max_count = 1) : on la retrouve par son type
        context['univers'] = UniversPage.objects.live().descendant_of(self).first()
        # Fiches à la une : on écarte une fiche SUPPRIMÉE depuis (le bloc garde
        # son numéro mais pointe vers le vide : None) ou DÉPUBLIÉE (le lien
        # mènerait à une 404). Sans ce tri, l'accueil entier plantait.
        context['fiches_a_la_une'] = [
            bloc.value for bloc in self.encyclopedie_a_la_une
            if bloc.value is not None and bloc.value.live
        ]
        # Les prestations (snippets) s'affichent dans la box Contact
        context['prestations'] = Prestation.objects.all()
        return context
