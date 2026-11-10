from django.db import models
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.blocks import PageChooserBlock  # utilisé par encyclopedie_a_la_une (à réactiver)
from wagtail.admin.panels import FieldPanel

from core.blocks import EmbedVideoBlock

class HomePage(Page):
    # 1. DIV EMBED : StreamField ou EmbedBlock
    video_embed = StreamField([
        ('video', EmbedVideoBlock()),
    ], use_json_field=True, blank=True)

    # 2. DIV UNIVERS : Lien vers la page Univers (dans l'app `pages`)
    page_univers = models.ForeignKey(
        'pages.StandardPage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Page Univers"
    )

    # # 3. DIV ENCYCLOPÉDIE : Sélection sur-mesure de fiches (dans l'app `encyclopedie`)
    # encyclopedie_a_la_une = StreamField([
    #     ('fiche_lore', PageChooserBlock(page_type='encyclopedie.LorePage', label="Fiche Lore")),
    # ], use_json_field=True, blank=True, verbose_name="Lore mis en avant")

    # 4. DIV CONTACT : Lien vers la page Contact (dans l'app `pages`)
    page_contact = models.ForeignKey(
        'pages.ContactPage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Page Contact"
    )

    # Configuration du panneau d'administration Wagtail
    content_panels = Page.content_panels + [
        FieldPanel('video_embed'),
        FieldPanel('page_univers'),
        # FieldPanel('encyclopedie_a_la_une'),
        FieldPanel('page_contact'),
    ]

    # # 5. DIV CAMPAGNES : Récupération automatique des enfants (app `campagnes`)
    # def get_context(self, request):
    #     context = super().get_context(request)
    #     # Import local pour éviter les imports circulaires
    #     from campagnes.models import CampagnePage
    #     # Récupère automatiquement toutes les sous-pages de type CampagnePage
    #     context['campagnes'] = CampagnePage.objects.child_of(self).live()
    #     return context