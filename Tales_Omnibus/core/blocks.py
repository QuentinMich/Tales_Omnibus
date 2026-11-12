# core/blocks.py
import re

from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock


class StreamPlayerBlock(blocks.StructBlock):
    """
    Lecteur de live : le client choisit la plateforme et donne juste sa chaîne.
    Le template fabrique le bon <iframe> (voir core/blocks/stream_player_block.html).
    """
    plateforme = blocks.ChoiceBlock(
        choices=[('twitch', 'Twitch'), ('youtube', 'YouTube')],
        default='twitch',
        label="Plateforme",
    )
    chaine = blocks.CharBlock(
        label="Chaîne",
        help_text=(
            "Twitch : le nom de la chaîne (ex. : talesomnibus). "
            "YouTube : l'ID de la chaîne, qui commence par « UC » "
            "(YouTube Studio > Paramètres > Chaîne > Paramètres avancés)."
        ),
    )
    titre = blocks.CharBlock(required=False, label="Titre affiché au-dessus du lecteur")

    def clean(self, value):
        # Vérifie le format de la chaîne selon la plateforme choisie,
        # pour afficher une erreur claire dans l'admin plutôt qu'un lecteur cassé.
        value = super().clean(value)
        chaine = value['chaine'].strip()
        if value['plateforme'] == 'twitch' and not re.fullmatch(r'\w{3,25}', chaine):
            erreur = "Un nom de chaîne Twitch ne contient que des lettres, chiffres et _ (3 à 25 caractères)."
        elif value['plateforme'] == 'youtube' and not re.fullmatch(r'UC[\w-]{22}', chaine):
            erreur = "Pour YouTube, il faut l'ID de la chaîne (24 caractères, commence par « UC »), pas le @pseudo."
        else:
            value['chaine'] = chaine
            return value
        raise StructBlockValidationError(block_errors={'chaine': ValidationError(erreur)})

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        # Twitch exige le domaine du site qui affiche le lecteur (paramètre "parent").
        # On le lit dans la requête, en enlevant le port (localhost:8000 -> localhost).
        request = (parent_context or {}).get('request')
        context['domaine'] = request.get_host().split(':')[0] if request else 'localhost'
        return context

    class Meta:
        template = "core/blocks/stream_player_block.html"
        icon = "media"
        label = "Lecteur de live (Twitch / YouTube)"


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