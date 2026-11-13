"""
TEXTE ALTERNATIF (ALT) AUTOMATIQUE DES IMAGES

Le client range ses images dans des dossiers : ce sont les COLLECTIONS de
Wagtail (menu Images > Collections), qui s'emboîtent comme un arbre :
    Personnage > Héros
Une image rangée là montre forcément un personnage, un héros. On s'en sert
pour écrire l'ALT tout seul, en trois morceaux :

    « Personnage, Héros : Brann le Rouquin. Une hache sur l'épaule. »
       └─ dossiers ─────┘  └─ titre ───────┘  └─ description ───┘

  - les dossiers : le chemin de la collection (sans la racine de Wagtail) ;
  - le titre de l'image : Wagtail le remplit avec le NOM DU FICHIER à
    l'envoi (on retire juste les « _ »), le client peut le corriger ;
  - la description (champ « Description » de l'image, facultatif) : les
    détails en plus, tapés à la main seulement si on en a envie.

Rien à taper pour avoir un ALT correct : une base existe toujours.

Fonction « pure » côté logique (une image en entrée, un texte en sortie),
utilisée dans les templates par le filtre {{ image|alt_auto }}.
"""
import re


def nettoyer_titre(titre):
    """« brann_le_rouquin » -> « brann le rouquin » (les tirets restent : Port-Lanterne)."""
    return re.sub(r"\s+", " ", (titre or "").replace("_", " ")).strip()


def dossiers_de(image):
    """Les noms des collections de l'image, de la plus large à la plus précise."""
    collection = getattr(image, 'collection', None)
    if collection is None:
        return []
    # depth 1 = la collection racine de Wagtail (« Root ») : pas un vrai dossier
    return [c.name for c in collection.get_ancestors(inclusive=True) if c.depth > 1]


def texte_alternatif(image):
    if image is None:
        return ""
    texte = nettoyer_titre(image.title)
    dossiers = dossiers_de(image)
    if dossiers:
        texte = f"{', '.join(dossiers)} : {texte}"
    description = (getattr(image, 'description', "") or "").strip()
    if description:
        texte = f"{texte.rstrip('.')}. {description}"
    return texte
