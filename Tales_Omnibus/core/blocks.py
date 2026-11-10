# core/blocks.py
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock

class EmbedVideoBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, label="Titre de la vidéo / live")
    video = EmbedBlock(label="Lien Twitch ou YouTube")

    class Meta:
        template = "core/blocks/embed_video_block.html"
        icon = "media"
        label = "Intégration Video/Stream"

class SingleImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(label="Image")
    caption = blocks.CharBlock(required=False, label="Légende")
    alt_text = blocks.CharBlock(required=False, label="Texte alternatif (SEO/Accessibilité)")

    class Meta:
        template = "core/blocks/single_image_block.html"
        icon = "image"
        label = "Image simple"

class BaseStreamBlock(blocks.StreamBlock):
    """
    Bloc réutilisable pour le StreamField des pages fixes (StandardPage, Univers, etc.)
    et autres contenus éditoriaux du site.
    """
    paragraph = blocks.RichTextBlock(
        icon="pilcrow",
        label="Paragraphe de texte",
        features=['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul', 'blockquote']
    )
    image = SingleImageBlock()
    embed = EmbedVideoBlock()
    
    class Meta:
        label = "Contenu de la page"