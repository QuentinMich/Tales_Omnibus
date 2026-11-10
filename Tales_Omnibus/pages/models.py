from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField

from core.blocks import BaseStreamBlock


# 1. Modèle pour la page standard (Univers, Mentions Légales, etc.)
class StandardPage(Page):
    intro = models.CharField(max_length=255, blank=True, verbose_name="Introduction")
    body = StreamField(BaseStreamBlock(), use_json_field=True, blank=True, verbose_name="Contenu")

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('body'),
    ]


# 2. Champs dynamiques du formulaire de contact
class ContactFormField(AbstractFormField):
    page = ParentalKey(
        'ContactPage',
        on_delete=models.CASCADE,
        related_name='form_fields'
    )


# 3. Modèle pour la page de contact
class ContactPage(AbstractEmailForm):
    intro = RichTextField(blank=True, verbose_name="Texte de présentation / Prestations")
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
