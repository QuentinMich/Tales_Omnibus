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


# Le tableau par défaut : les 6 caractéristiques de D&D, sur une ligne
STATS_DND = ["Force", "Dextérité", "Constitution", "Intelligence", "Sagesse", "Charisme"]


class StatBlock(blocks.StructBlock):
    """Une case du tableau : « Force / 15 / +2 »."""
    libelle = blocks.CharBlock(label="Caractéristique", max_length=40)
    # Du texte et pas un nombre : « 15 », « 45 % », « 3d6 », « — »… selon le jeu
    valeur = blocks.CharBlock(required=False, label="Valeur", max_length=12)
    complement = blocks.CharBlock(
        required=False, label="Sous la valeur", max_length=12,
        help_text="Facultatif : le modificateur de D&D (« +2 »), un maximum…",
    )


class TableauDeStatsBlock(blocks.StructBlock):
    """
    Un tableau de caractéristiques, adaptable à tous les jeux :
      - D&D : 6 cases sur 1 ligne (le modèle par défaut) ;
      - Warhammer : une dizaine de cases, sur 1 ou 2 lignes ;
      - un système à 30 compétences : 6 colonnes et des petites cases.
    On choisit le nombre de COLONNES ; les lignes se font toutes seules
    (10 cases sur 5 colonnes = 2 lignes). Aucune case = rien d'affiché.
    """
    titre = blocks.CharBlock(required=False, default="Caractéristiques", label="Titre")
    colonnes = blocks.IntegerBlock(
        default=6, min_value=1, max_value=12, label="Nombre de colonnes",
        help_text="Les lignes se calculent toutes seules. Sur téléphone, ça s'adapte à l'écran.",
    )
    taille = blocks.ChoiceBlock(
        choices=[('grande', "Grandes cases"), ('moyenne', "Moyennes"), ('petite', "Petites (beaucoup de stats)")],
        default='grande', label="Taille des cases",
    )
    stats = blocks.ListBlock(
        StatBlock(),
        default=[{'libelle': nom, 'valeur': "", 'complement': ""} for nom in STATS_DND],
        label="Cases",
    )

    class Meta:
        template = "core/blocks/tableau_de_stats_block.html"
        icon = "table"
        label = "Tableau de caractéristiques"


class SeparateurBlock(blocks.StaticBlock):
    """Un trait de séparation entre deux parties (balise <hr>). Rien à remplir."""

    class Meta:
        template = "core/blocks/separateur_block.html"
        icon = "horizontalrule"
        label = "Séparateur"
        admin_text = "Trait de séparation entre deux parties."


class EnluminureBlock(blocks.StructBlock):
    """
    Un passage ENLUMINÉ, comme dans un manuscrit : grande lettrine décorée au
    début du texte, et selon l'ornement choisi, une bordure dans la marge ou
    un cadre. Sans thème, la lettrine est simplement grande et colorée ; c'est
    le thème qui ajoute la feuille d'or, les rinceaux, etc.
    """
    ORNEMENTS = [
        ("lettrine", "Lettrine seule"),
        ("marge", "Lettrine + rinceaux dans la marge"),
        ("cadre", "Lettrine + page encadrée"),
    ]
    ornement = blocks.ChoiceBlock(choices=ORNEMENTS, default="lettrine", label="Ornement")
    texte = blocks.RichTextBlock(
        label="Texte",
        help_text="La première lettre du premier paragraphe devient la lettrine.",
        features=['bold', 'italic', 'link', 'blockquote'],
    )

    class Meta:
        template = "core/blocks/enluminure_block.html"
        icon = "openquote"
        label = "Enluminure (lettrine décorée)"


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
    enluminure = EnluminureBlock()
    embed = EmbedVideoBlock()

    class Meta:
        label = "Contenu de la page"
