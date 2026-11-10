from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel

from core.models import BaseFichePage  # Ajuste l'import selon l'emplacement de BaseFichePage


# 1. Modèle de Tag relié à la vraie classe LorePage (non-abstraite)
class LorePageTag(TaggedItemBase):
    content_object = ParentalKey(
        'LorePage',
        on_delete=models.CASCADE,
        related_name='tagged_items'
    )


# 2. La classe LorePage
class LorePage(BaseFichePage):
    tags = ClusterTaggableManager(through=LorePageTag, blank=True)

    content_panels = BaseFichePage.content_panels + [
        FieldPanel('tags'),
    ]