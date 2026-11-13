# core/blocks.py
import re

from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.documents.blocks import DocumentChooserBlock
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
    # Gauche / droite : le texte qui suit s'enroule autour de l'image.
    # Les images déjà enregistrées sans ce choix prennent la valeur par défaut.
    position = blocks.ChoiceBlock(
        choices=[
            ('centre', "Centrée"),
            ('gauche', "À gauche, texte autour"),
            ('droite', "À droite, texte autour"),
            ('large', "Pleine largeur"),
        ],
        default='centre',
        label="Position",
    )

    class Meta:
        template = "core/blocks/single_image_block.html"
        icon = "image"
        label = "Image simple"

class SectionBlock(blocks.StructBlock):
    """
    Un ARTICLE de la page : un titre + son texte, rendu dans une vraie balise
    <section> avec un <h2>. Pour les moteurs de recherche (et les lecteurs
    d'écran), la page est ainsi découpée en parties nommées : h1 = la fiche,
    h2 = chaque section, h3 = les sous-parties dans le texte.
    """
    titre = blocks.CharBlock(label="Titre de la section")
    texte = blocks.RichTextBlock(
        label="Texte",
        # Pas de h2 ici : c'est le titre de la section ; h3 pour les sous-parties
        features=['h3', 'bold', 'italic', 'link', 'ol', 'ul', 'blockquote'],
    )

    class Meta:
        template = "core/blocks/section_block.html"
        icon = "doc-full"
        label = "Section (titre + texte)"


class DocumentBlock(blocks.StructBlock):
    """
    Une AIDE DE JEU à télécharger (handout) : lettre, plan, règles maison…
    Le fichier vient de la bibliothèque « Documents » de Wagtail (PDF, DOCX,
    ODT, ZIP… voir WAGTAILDOCS_EXTENSIONS dans les settings).
    Sur le site : une carte avec le type et le poids du fichier, et un bouton.
    """
    document = DocumentChooserBlock(label="Document")
    titre = blocks.CharBlock(
        required=False, label="Titre",
        help_text="Vide : on reprend le titre du document.",
    )
    description = blocks.TextBlock(
        required=False, label="Description",
        help_text="Facultatif : « La lettre trouvée sur le cadavre du messager »…",
    )

    class Meta:
        template = "core/blocks/document_block.html"
        icon = "doc-full-inverse"
        label = "Document à télécharger (aide de jeu)"


class SeparateurBlock(blocks.StaticBlock):
    """Un trait de séparation entre deux parties (balise <hr>). Rien à remplir."""

    class Meta:
        template = "core/blocks/separateur_block.html"
        icon = "horizontalrule"
        label = "Séparateur"
        admin_text = "Trait de séparation entre deux parties."


class BaseStreamBlock(blocks.StreamBlock):
    """
    Bloc réutilisable pour le StreamField des pages fixes (Univers, fiches, etc.)
    et autres contenus éditoriaux du site : de quoi construire de vrais articles.
    """
    section = SectionBlock()
    paragraph = blocks.RichTextBlock(
        icon="pilcrow",
        label="Paragraphe de texte",
        features=['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul', 'blockquote']
    )
    image = SingleImageBlock()
    document = DocumentBlock()
    separateur = SeparateurBlock()
    embed = EmbedVideoBlock()

    class Meta:
        label = "Contenu de la page"
