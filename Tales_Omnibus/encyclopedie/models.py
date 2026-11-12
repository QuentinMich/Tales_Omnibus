from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from core.models import BaseFichePage


# 1. INDEX DE L'ENCYCLOPÉDIE (conteneur des fiches Lore)
class EncyclopedieIndexPage(Page):
    intro = RichTextField(
        blank=True,
        features=['bold', 'italic', 'link'],
        verbose_name="Présentation de l'encyclopédie"
    )

    subpage_types = ['encyclopedie.LorePage']
    parent_page_types = ['home.HomePage']
    max_count = 1  # Une seule encyclopédie pour tout l'univers

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['fiches'] = LorePage.objects.child_of(self).live().order_by('title')
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
    tags = ClusterTaggableManager(through=LorePageTag, blank=True)

    subpage_types = []  # Page feuille
    parent_page_types = ['encyclopedie.EncyclopedieIndexPage']

    content_panels = BaseFichePage.content_panels + [
        FieldPanel('tags'),
    ]
