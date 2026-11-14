"""
LA DÉMO : une campagne de démonstration complète, pour voir toutes les
fonctionnalités du site (et servir d'exemple à suivre au nouveau MJ).

Une seule logique, deux façons de la lancer (comme l'entretien) :
  - en ligne de commande : manage.py creer_demo  /  creer_demo --supprimer
  - dans l'admin : page « Bien démarrer » (boutons Ajouter / Retirer la démo)

Contenu : une campagne « Les Brumes d'Ardenn » (2 cartes, une chronologie,
3 héros), des lieux et des fiches Lore dans l'encyclopédie, un arbre de
catégories, des familles de tags, des tags, des fiches épinglées, un lieu
présent sur deux cartes, des articles (sections, images positionnées,
séparateurs, enluminures), du Lore présent dans la campagne, une aide de jeu…

IMAGES : si les fichiers de core/donnees_demo/images/ existent (voir le
LISEZMOI.md de ce dossier), la démo les importe dans la médiathèque, chacune
rangée dans son DOSSIER (collection), avec titre et description (donc un ALT
automatique propre), et les pose sur les bonnes pages. Il manque un fichier ?
La démo réutilise les images déjà présentes sur le site, à tour de rôle.

Tout le contenu est DÉCLARÉ ci-dessous : c'est ce qui permet de retirer
exactement ce que la démo a créé, sans toucher aux vraies pages. Les images
de démo portent un tag (TAG_IMAGES) : on les retrouve et on les retire.
Les catégories et les dossiers, eux, sont conservés : ce sont des
rangements réutilisables.
"""
from pathlib import Path

from django.core.files import File
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify
from taggit.models import Tag
from wagtail.documents import get_document_model
from wagtail.images.models import Image
from wagtail.models import Collection

from campagnes.models import (
    Apparition, CampagnePage, CampagnesIndexPage, CartePage, ChronologiePage, EvenementPage, HeroPage, LieuPage,
)
from core.models import Categorie
from encyclopedie.models import EncyclopedieIndexPage, FamilleDeTags, LorePage, PresenceEnCampagne


class DemoImpossible(Exception):
    """Une raison lisible de ne pas créer / retirer la démo (affichée telle quelle)."""


CAMPAGNE = "Les Brumes d'Ardenn"

# --- Une aide de jeu (document à télécharger), rangée dans « Aide de jeu » ---
AIDE_DE_JEU = "Lettre du messager"
TEXTE_AIDE_DE_JEU = (
    "Au Capitaine de Fort-Sombre,\n\n"
    "Les lanternes de Port-Lanterne se sont tournées vers le nord cette nuit.\n"
    "Toutes. En même temps. Je ne sais pas ce qu'elles regardent, mais je sais\n"
    "qu'elles ont cligné.\n\n"
    "Ne faites confiance à aucun corbeau qui parle trop bien.\n\n"
    "— Un ami de la Guilde\n"
)

# --- Arbre des catégories : (nom, parent, couleur, défaut pour) --------------
CATEGORIES = [
    ("Personnage", None, "#A23B3B", None),
    ("Héros", "Personnage", "", 'heros'),
    ("PNJ", "Personnage", "", None),
    ("Déité", "Personnage", "#8A6D0B", None),
    ("Déité majeure", "Déité", "", None),
    ("Déité mineure", "Déité", "", None),
    ("Créature", "Personnage", "#2E7D32", None),
    ("Lieu", None, "#3B6EA2", 'lieux'),
    ("Continent", "Lieu", "", None),
    ("Royaume", "Lieu", "", None),
    ("Région", "Lieu", "#4F7942", None),
    ("Ville", "Lieu", "#1E88E5", None),
    ("Village", "Lieu", "", None),
    ("Lieu-dit", "Lieu", "#5C6BC0", None),
    ("Événement", None, "#4E8A3E", 'evenements'),
    ("Bataille", "Événement", "#B23A2B", None),
    ("Fête", "Événement", "#E0A100", None),
    ("Catastrophe", "Événement", "", None),
    ("Divers", None, "#6B4C9A", 'lore'),
    ("Faction", "Divers", "", None),
    ("Objet", "Divers", "", None),
    ("Légende", "Divers", "", None),
]

# --- Familles de tags : nom -> (couleur, ordre, tags) -------------------------
FAMILLES = {
    "Créatures": ("#2E7D32", 1, ["dragon", "loup-garou", "esprit"]),
    "Factions": ("#C77700", 2, ["Ordre du Corbeau", "Guilde des Brumes"]),
    "Magie": ("#1565C0", 3, ["runes", "malédiction", "prophétie"]),
}

# --- Lieux (encyclopédie) : titre -> (catégorie, intro, tags, épinglé) --------
LIEUX = {
    "Ardenn": ("Continent", "Un continent noyé de brumes, où les routes changent de place la nuit.", ["prophétie"], True),
    "Royaume du Val Gris": ("Royaume", "Un royaume caché derrière un rideau de brouillard magique.", ["Guilde des Brumes"], False),
    "Port-Lanterne": ("Ville", "La seule ville où les lanternes ne s'éteignent jamais. On dit qu'elles regardent.", ["Guilde des Brumes", "esprit"], False),
    "Fort-Sombre": ("Lieu-dit", "Une forteresse en ruines. Les corbeaux y sont plus nombreux que les pierres.", ["Ordre du Corbeau", "malédiction"], False),
    "Hameau des Saules": ("Village", "Trois maisons, un puits, et un saule qui chante quand il pleut.", ["esprit"], False),
    "Bois des Murmures": ("Région", "Une forêt où les arbres se répètent des secrets. Mal, en général.", ["esprit"], False),
    "Terres Brûlées": ("Région", "Ce qu'il reste après le passage du Dragon de Suie. Personne n'en revendique un seul caillou.", ["dragon", "malédiction"], False),
}

# --- Apparitions : (carte, lieu, position, à cette époque) -------------------
# position = (x, y) pour un point, une liste de sommets pour une zone, ou None.
# Les zones rangent les lieux toutes seules à la publication de la carte :
# ici, Hameau des Saules est dans le Bois des Murmures, lui-même dans Ardenn.
APPARITIONS = [
    # Calées sur core/donnees_demo/images/carte-ardenn.jpg (en % de l'image) :
    # le continent, la forêt au sud-ouest, la plaine brûlée au nord-est
    ("Carte d'Ardenn", "Ardenn", [[64, 0], [100, 0], [100, 72], [88, 69], [68, 68], [60, 72], [50, 77], [35, 80],
                                  [25, 86], [14, 94], [10, 86], [11, 64], [22, 55], [28, 50], [29, 42], [22, 32],
                                  [28, 22], [40, 16], [55, 8]], ""),
    ("Carte d'Ardenn", "Bois des Murmures", [[17, 62], [27, 58], [40, 64], [51, 72], [45, 78], [33, 82], [22, 88],
                                             [14, 90], [13, 75]], ""),
    ("Carte d'Ardenn", "Terres Brûlées", [[58, 10], [78, 8], [98, 10], [98, 28], [85, 34], [70, 33], [57, 28],
                                          [55, 18]], "Un no man's land : ni l'Ordre ni la Guilde n'y mettent les pieds."),
    ("Carte d'Ardenn", "Port-Lanterne", (33, 48), ""),  # le port, à l'embouchure du fleuve
    ("Carte d'Ardenn", "Fort-Sombre", (78, 52), "Encore debout, tenu par l'Ordre du Corbeau."),  # sur sa colline
    ("Carte d'Ardenn", "Hameau des Saules", (38, 70), ""),  # une clairière du Bois des Murmures
    # Calées sur carte-val-gris.jpg : la vallée, dans son anneau de montagnes
    ("Carte du Val Gris", "Royaume du Val Gris", [[20, 28], [47, 23], [67, 20], [84, 28], [89, 40], [80, 54],
                                                  [67, 65], [45, 67], [28, 63], [20, 47]],
     "Caché par le brouillard : aucune carte du monde ne le montre."),
    ("Carte du Val Gris", "Port-Lanterne", (57, 59), "Reconstruit après le Grand Brouillard."),  # les maisons au bord du torrent
    ("Carte du Val Gris", "Fort-Sombre", None, ""),  # ajouté à la carte mais pas encore placé
]

# --- Style de certaines zones : (carte, lieu) -> champs de l'Apparition -------
STYLES_DE_ZONES = {
    # Hachurée, frontière en tirets, et nom placé à la main sur le cœur du
    # brasier (exemple du bouton « Placer le centre » de l'éditeur de carte)
    ("Carte d'Ardenn", "Terres Brûlées"): {'motif': 'hachures', 'bordure': 'tirets',
                                           'centre_manuel': True, 'coord_x': 80, 'coord_y': 20},
    ("Carte du Val Gris", "Royaume du Val Gris"): {'bordure': 'tirets'},  # frontière floue, dans la brume
}

# --- Fiches Lore : titre -> (catégorie, intro, tags, épinglé) -----------------
LORE = {
    "Vaël, déesse des Brumes": ("Déité majeure", "Elle tisse le brouillard et décide qui s'y perd.", ["prophétie", "esprit"], True),
    "Kroth le Petit": ("Déité mineure", "Dieu des clés perdues. Il les garde, évidemment.", ["runes"], False),
    "L'Ordre du Corbeau": ("Faction", "Des chevaliers qui ne parlent qu'aux oiseaux. Les oiseaux, eux, parlent beaucoup.", ["Ordre du Corbeau"], False),
    "Le Marchand Borgne": ("PNJ", "Il vend de tout, surtout ce qu'il n'a pas. Son œil manquant est à vendre aussi.", ["Guilde des Brumes", "pouet"], False),
    "Le Dragon de Suie": ("Créature", "Un dragon fait de fumée. Il éternue des incendies.", ["dragon", "malédiction"], True),
    "L'Épée sans Nom": ("Objet", "Une épée qui refuse qu'on la nomme. Le dernier qui a essayé s'appelle désormais « Machin ».", ["runes", "malédiction"], False),
    "La Légende du Lac Gris": ("Légende", "Au fond du lac dort un royaume entier. Il ronfle.", ["esprit", "prophétie"], False),
    # Sans catégorie : cette fiche tombe dans la catégorie par défaut du Lore (« Divers »)
    "Notes du MJ": (None, "Des notes griffonnées entre deux séances. Une tache de café cache la moitié des secrets.", ["pouet"], False),
}

# --- Lore présent dans la campagne : titre -> ce qui est propre à la campagne
PRESENCES = {
    "Vaël, déesse des Brumes": "Vénérée en secret depuis le Grand Brouillard. Ses prêtres portent des lanternes éteintes.",
    "L'Ordre du Corbeau": "Ils tiennent Fort-Sombre et contrôlent les routes du nord.",
    "Le Dragon de Suie": "Endormi sous les cendres de Fort-Sombre. Pour l'instant.",
}

# --- Chronologie : titre -> (catégorie, date_ordre, date affichée, lieu, intro, tags)
EVENEMENTS = {
    "La Nuit des Cendres": ("Bataille", -12, "An -12, nuit du solstice", "Fort-Sombre",
                            "Le Dragon de Suie attaque le fort. Personne ne gagne, tout le monde tousse.", ["dragon", "Ordre du Corbeau"]),
    "Le Grand Brouillard": ("Catastrophe", 0, "An 0", "Ardenn",
                            "La brume recouvre le continent. Le calendrier repart de zéro, par commodité.", ["prophétie"]),
    "Le Bal des Lanternes": ("Fête", 3, "An 3, premier jour du printemps", "Port-Lanterne",
                             "Une fête où chacun danse avec une lanterne. Certaines lanternes dansent mieux.", ["esprit", "pouet"]),
    # Sans catégorie : cet événement tombe dans la catégorie par défaut (« Événement »)
    "Le Pacte du Corbeau": (None, 7, "An 7", "Fort-Sombre",
                            "L'Ordre jure de protéger Port-Lanterne. Les corbeaux, eux, n'ont rien juré.", ["Ordre du Corbeau", "runes"]),
}

# --- Héros : titre -> (catégorie, joueur, lieu d'origine, intro, tags, épinglé)
def tableau(titre, colonnes, taille, stats):
    """Un tableau de caractéristiques : stats = [(libellé, valeur, complément), …]."""
    return ('tableau', {
        'titre': titre, 'colonnes': colonnes, 'taille': taille,
        'stats': [{'libelle': l, 'valeur': v, 'complement': c} for l, v, c in stats],
    })


# --- Caractéristiques des héros : trois cas à montrer -------------------------
STATS_DES_HEROS = {
    # D&D, le modèle par défaut, rempli
    "Maëlis Ventcourt": [tableau("Caractéristiques", 6, 'grande', [
        ("Force", "8", "-1"), ("Dextérité", "14", "+2"), ("Constitution", "12", "+1"),
        ("Intelligence", "17", "+3"), ("Sagesse", "13", "+1"), ("Charisme", "10", "+0"),
    ])],
    # Un système à la Warhammer : 10 caractéristiques en %, sur 2 lignes,
    # puis un 2e tableau de compétences en petites cases
    "Brann le Rouquin": [
        tableau("Profil", 5, 'moyenne', [
            ("Capacité de combat", "45", ""), ("Capacité de tir", "30", ""), ("Force", "40", ""),
            ("Endurance", "42", ""), ("Initiative", "35", ""), ("Agilité", "33", ""),
            ("Dextérité", "28", ""), ("Intelligence", "25", ""), ("Force mentale", "38", ""),
            ("Sociabilité", "31", ""),
        ]),
        tableau("Compétences", 6, 'petite', [
            ("Bûcheronnage", "55", ""), ("Intimidation", "40", ""), ("Pistage", "35", ""),
            ("Résistance", "50", ""), ("Survie", "45", ""), ("Hache hantée", "?", "elle refuse"),
        ]),
    ],
    # Sœur Ysolde : aucun tableau, rien ne s'affiche
}

# --- Caractéristiques de fiches Lore (créatures, PNJ) : facultatives ---------
STATS_DU_LORE = {
    "Le Dragon de Suie": [tableau("Caractéristiques", 6, 'grande', [
        ("Force", "23", "+6"), ("Dextérité", "10", "+0"), ("Constitution", "21", "+5"),
        ("Intelligence", "14", "+2"), ("Sagesse", "11", "+0"), ("Charisme", "19", "+4"),
    ]), tableau("Combat", 3, 'moyenne', [
        ("Classe d'armure", "19", ""), ("Points de vie", "207", ""), ("Souffle de suie", "16d6", "1 fois / jour"),
    ])],
    "Le Marchand Borgne": [tableau("Caractéristiques", 6, 'moyenne', [
        ("Force", "9", "-1"), ("Dextérité", "12", "+1"), ("Constitution", "10", "+0"),
        ("Intelligence", "15", "+2"), ("Sagesse", "16", "+3"), ("Charisme", "18", "+4"),
    ])],
}

# titre -> (catégorie, joueur, lieu d'origine, accroche, tags, épinglée, joué par, a quitté le groupe)
# Les quatre cas de la page Campagne : trois héros de joueurs (la rangée du
# groupe), un compagnon de route joué par le MJ, un ancien membre.
HEROS = {
    "Maëlis Ventcourt": ("Héros", "Joueuse A", "Port-Lanterne",
                         "Une cartographe qui dessine les routes avant qu'elles bougent.", ["runes", "prophétie"], True,
                         'joueur', False),
    "Brann le Rouquin": ("Héros", "Joueur B", "Hameau des Saules",
                         "Un bûcheron convaincu que son hache est hantée. Elle l'est.", ["esprit", "pouet"], False,
                         'joueur', False),
    "Pip Chardon": ("Héros", "Joueuse C", "Port-Lanterne",
                    "Une voleuse halfeline qui jure n'avoir jamais rien volé. Ses poches disent le contraire.",
                    ["lanternes"], False, 'joueur', False),
    "Sœur Ysolde": ("PNJ", "", "Fort-Sombre",
                    # Fiche Héros jouée par le MJ et catégorie « PNJ » : un compagnon de route
                    # sur la page Campagne, rangée avec les PNJ dans l'encyclopédie
                    "Une nonne de l'Ordre du Corbeau, qui suit le groupe « pour son salut ». Le sien, surtout.",
                    ["Ordre du Corbeau"], False, 'mj', False),
    "Gaspard Têtenoire": ("Héros", "Joueur D", "Fort-Sombre",
                          "Un mercenaire bougon, parti un matin sans un mot (son joueur a déménagé à Lyon).",
                          ["esprit"], False, 'joueur', True),
}


# --- Images de la démo ---------------------------------------------------------
# clé -> (nom du fichier SANS extension, titre, dossier, description)
# Le fichier peut être en .jpg, .jpeg, .png, .webp ou .svg. Le dossier est un
# chemin de collections Wagtail (« Lieu/Ville ») : créé s'il n'existe pas.
# Titre + dossier + description = l'ALT automatique (core/images.py).
DOSSIER_IMAGES = Path(__file__).resolve().parent / "donnees_demo" / "images"
EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".svg")
TAG_IMAGES = "demo-tales-omnibus"

IMAGES = {
    # La campagne
    "banniere": ("banniere-brumes-ardenn", "Les Brumes d'Ardenn", "Site",
                 "Un continent noyé de brume, des lanternes au loin."),
    # Les cartes
    "carte-ardenn": ("carte-ardenn", "Carte d'Ardenn", "Lieu/Carte",
                     "Carte du continent, dessinée à la main avant le Grand Brouillard."),
    "carte-val-gris": ("carte-val-gris", "Carte du Val Gris", "Lieu/Carte",
                       "Carte d'un royaume caché dans la brume, tracée par un survivant."),
    # Les héros
    "heros-maelis-ventcourt": ("heros-maelis-ventcourt", "Maëlis Ventcourt", "Personnage/Héros",
                               "Une jeune cartographe, carnet et compas à la main."),
    "heros-brann-le-rouquin": ("heros-brann-le-rouquin", "Brann le Rouquin", "Personnage/Héros",
                               "Un bûcheron roux et massif, une hache aux reflets fantomatiques."),
    "heros-pip-chardon": ("heros-pip-chardon", "Pip Chardon", "Personnage/Héros",
                          "Une petite voleuse aux poches pleines, sourire innocent."),
    # Jouée par le MJ, mais c'est une fiche Héros : rangée avec les héros
    "heros-soeur-ysolde": ("heros-soeur-ysolde", "Sœur Ysolde", "Personnage/Héros",
                           "Une nonne en robe noire, un corbeau sur l'épaule."),
    "heros-gaspard-tetenoire": ("heros-gaspard-tetenoire", "Gaspard Têtenoire", "Personnage/Héros",
                                "Un mercenaire bougon en armure cabossée, de dos sur la route."),
    # Les lieux
    "lieu-ardenn": ("lieu-ardenn", "Ardenn", "Lieu/Paysage",
                    "Un continent de collines et de forêts, mangé par la brume."),
    "lieu-royaume-du-val-gris": ("lieu-royaume-du-val-gris", "Royaume du Val Gris", "Lieu/Paysage",
                                 "Une vallée et ses tours, derrière un rideau de brouillard."),
    "lieu-port-lanterne": ("lieu-port-lanterne", "Port-Lanterne", "Lieu/Ville",
                           "Un port la nuit, des centaines de lanternes allumées."),
    "lieu-fort-sombre": ("lieu-fort-sombre", "Fort-Sombre", "Lieu/Ville",
                         "Une forteresse en ruines couverte de corbeaux."),
    "lieu-hameau-des-saules": ("lieu-hameau-des-saules", "Hameau des Saules", "Lieu/Ville",
                               "Trois maisons, un puits et un grand saule sous la pluie."),
    "lieu-bois-des-murmures": ("lieu-bois-des-murmures", "Bois des Murmures", "Lieu/Paysage",
                               "Une forêt ancienne et sombre, des arbres aux troncs tordus."),
    "lieu-terres-brulees": ("lieu-terres-brulees", "Terres Brûlées", "Lieu/Paysage",
                            "Une plaine noircie, des arbres calcinés et de la cendre."),
    # Le Lore
    "lore-vael-deesse-des-brumes": ("lore-vael-deesse-des-brumes", "Vaël, déesse des Brumes", "Personnage/Déité",
                                    "Une déesse faite de brume, une lanterne éteinte à la main."),
    "lore-kroth-le-petit": ("lore-kroth-le-petit", "Kroth le Petit", "Personnage/Déité",
                            "Un petit dieu bedonnant couvert de trousseaux de clés."),
    "lore-lordre-du-corbeau": ("lore-lordre-du-corbeau", "L'Ordre du Corbeau", "Personnage/PNJ",
                               "Des chevaliers en armure noire, des corbeaux sur les épaules."),
    "lore-le-marchand-borgne": ("lore-le-marchand-borgne", "Le Marchand Borgne", "Personnage/PNJ",
                                "Un marchand borgne derrière un étal encombré de bibelots."),
    "lore-le-dragon-de-suie": ("lore-le-dragon-de-suie", "Le Dragon de Suie", "Personnage/Créature",
                               "Un dragon fait de fumée noire, des braises à la place des yeux."),
    "lore-lepee-sans-nom": ("lore-lepee-sans-nom", "L'Épée sans Nom", "Objet",
                            "Une épée gravée de runes, plantée dans une pierre."),
    "lore-la-legende-du-lac-gris": ("lore-la-legende-du-lac-gris", "La Légende du Lac Gris", "Lieu/Paysage",
                                    "Un lac immobile, les toits d'une ville engloutie sous l'eau."),
    # La chronologie
    "evenement-la-nuit-des-cendres": ("evenement-la-nuit-des-cendres", "La Nuit des Cendres", "Événement",
                                      "Une forteresse en flammes sous un dragon de fumée."),
    "evenement-le-grand-brouillard": ("evenement-le-grand-brouillard", "Le Grand Brouillard", "Événement",
                                      "Un mur de brume qui avale une vallée entière."),
    "evenement-le-bal-des-lanternes": ("evenement-le-bal-des-lanternes", "Le Bal des Lanternes", "Événement",
                                       "Des danseurs sur une place, chacun une lanterne à la main."),
    "evenement-le-pacte-du-corbeau": ("evenement-le-pacte-du-corbeau", "Le Pacte du Corbeau", "Événement",
                                      "Des chevaliers à genoux prêtent serment devant un corbeau."),
    # Les illustrations des articles (gravures, dans le corps des fiches Lore)
    "gravure-erudit": ("gravure-erudit", "Gravure d'un érudit", "Site",
                       "Gravure ancienne : un érudit penché sur un grimoire à la chandelle."),
    "gravure-bestiaire": ("gravure-bestiaire", "Page de bestiaire", "Site",
                          "Gravure ancienne : une page de bestiaire couverte de créatures."),
    # Les icônes de catégories (sur les cartes, un point = l'icône seule)
    "icone-ville": ("icone-ville", "Ville", "Site/Icône", ""),
    "icone-village": ("icone-village", "Village", "Site/Icône", ""),
    "icone-lieu-dit": ("icone-lieu-dit", "Lieu-dit", "Site/Icône", ""),
}

# Le POINT FOCAL de Wagtail (en % de l'image : centre x, centre y, largeur,
# hauteur de la zone à garder) : les rendus « fill-… » recadrent AUTOUR de
# lui. Sans lui, Wagtail recadre au centre, et une vignette en paysage d'un
# portrait coupe le visage. Relevé à l'œil sur chaque image (le visage, la
# créature, la scène). Une image absente de ce dictionnaire : le centre suffit.
POINTS_FOCAUX = {
    "heros-maelis-ventcourt": (50, 23, 20, 15),
    "heros-brann-le-rouquin": (50, 28, 25, 20),
    "heros-pip-chardon": (50, 46, 20, 15),
    "heros-soeur-ysolde": (50, 39, 20, 15),
    "heros-gaspard-tetenoire": (52, 40, 30, 30),
    "lore-vael-deesse-des-brumes": (50, 24, 20, 15),
    "lore-kroth-le-petit": (51, 28, 20, 15),
    "lore-lordre-du-corbeau": (50, 30, 30, 20),
    "lore-le-marchand-borgne": (52, 28, 20, 15),
    "lore-le-dragon-de-suie": (40, 41, 30, 25),
    "lore-lepee-sans-nom": (50, 45, 30, 50),
    "lore-la-legende-du-lac-gris": (50, 62, 60, 30),
    "evenement-la-nuit-des-cendres": (50, 35, 40, 40),
    "evenement-le-bal-des-lanternes": (50, 55, 60, 40),
    "evenement-le-pacte-du-corbeau": (50, 40, 30, 30),
    "gravure-erudit": (58, 38, 30, 25),
}


def slug_de_fichier(titre):
    """
    slugify(), mais sans perdre les ligatures : Django SUPPRIME « œ » et « æ »
    (ce ne sont pas des lettres accentuées), « Sœur » donnerait « sur ».
    """
    for ligature, lettres in (("œ", "oe"), ("Œ", "Oe"), ("æ", "ae"), ("Æ", "Ae")):
        titre = titre.replace(ligature, lettres)
    return slugify(titre)


def poser_le_point_focal(image, cle):
    """Convertit le point focal déclaré (en %) en pixels, l'unité de Wagtail."""
    if cle not in POINTS_FOCAUX or not image.width or image.focal_point_x is not None:
        return  # pas déclaré, image sans taille (SVG), ou déjà réglé à la main
    x, y, largeur, hauteur = POINTS_FOCAUX[cle]
    image.focal_point_x = round(image.width * x / 100)
    image.focal_point_y = round(image.height * y / 100)
    image.focal_point_width = round(image.width * largeur / 100)
    image.focal_point_height = round(image.height * hauteur / 100)
    image.save(update_fields=["focal_point_x", "focal_point_y", "focal_point_width", "focal_point_height"])

# Quelle catégorie reçoit quelle icône (seulement si elle n'en a pas déjà une)
ICONES_DES_CATEGORIES = {"Ville": "icone-ville", "Village": "icone-village", "Lieu-dit": "icone-lieu-dit"}


def fichier_image(nom):
    """Le fichier d'une image de démo, quelle que soit son extension (ou None)."""
    for extension in EXTENSIONS:
        chemin = DOSSIER_IMAGES / f"{nom}{extension}"
        if chemin.is_file():
            return chemin
    return None


def dossier(chemin):
    """La collection « Lieu/Ville » : créée (avec ses parents) si elle manque."""
    courant = Collection.get_first_root_node()
    for nom in chemin.split("/"):
        enfant = courant.get_children().filter(name=nom).first()
        courant = enfant or courant.add_child(name=nom)
    return courant


def importer_les_images():
    """
    Importe dans la médiathèque les images de démo PRÉSENTES dans le dossier,
    et renvoie {clé: Image}. Une image déjà importée (même titre, tag de
    démo) est réutilisée : on peut relancer sans doublon.
    """
    importees = {}
    for cle, (nom, titre, chemin, description) in IMAGES.items():
        fichier = fichier_image(nom)
        if fichier is None:
            continue
        image = Image.objects.filter(title=titre, tags__name=TAG_IMAGES).first()
        if image is None:
            with fichier.open("rb") as contenu:
                image = Image(title=titre, description=description, collection=dossier(chemin))
                image.file.save(fichier.name, File(contenu), save=False)
                image.save()
            image.tags.add(TAG_IMAGES)
        poser_le_point_focal(image, cle)
        importees[cle] = image
    return importees


def demo_installee():
    return CampagnePage.objects.filter(title=CAMPAGNE).exists()


def images_de_demo_disponibles():
    """(nombre de fichiers présents, nombre attendu) : pour la page Bien démarrer."""
    return sum(1 for nom, *_ in IMAGES.values() if fichier_image(nom)), len(IMAGES)


# ---------------------------------------------------------------------- création
def creer_demo():
    """Crée la démo et renvoie une phrase de compte rendu. Lève DemoImpossible."""
    index = CampagnesIndexPage.objects.first()
    encyclopedie = EncyclopedieIndexPage.objects.first()
    if not index or not encyclopedie:
        raise DemoImpossible("Il faut d'abord les pages « Campagnes » et « Encyclopédie » "
                             "(bouton « Créer la structure du site »).")
    if demo_installee():
        raise DemoImpossible("La démo est déjà installée.")
    # transaction.atomic : si quoi que ce soit plante, RIEN n'est créé
    # (pas de démo à moitié construite dans la base).
    with transaction.atomic():
        nb_images = _creer(index, encyclopedie)
    return (f"Démo installée : la campagne « {CAMPAGNE} », ses fiches et "
            f"{nb_images} image(s) de démo rangées dans leurs dossiers.")


def _creer(index, encyclopedie):
    cats = _creer_categories()
    _creer_familles()
    demo = importer_les_images()
    for nom_categorie, cle in ICONES_DES_CATEGORIES.items():
        categorie = cats.get(nom_categorie)
        if categorie and not categorie.icone and cle in demo:
            categorie.icone = demo[cle]
            categorie.save(update_fields=["icone"])

    # Les images déjà sur le site : en secours quand une image de démo manque
    ids_demo = {image.pk for image in demo.values()}
    images = [i for i in Image.objects.all() if i.pk not in ids_demo]
    portraits = [i for i in images if i.height > i.width and "carte" not in i.title.lower()] or images
    gravures = [demo[c] for c in ("gravure-erudit", "gravure-bestiaire") if c in demo]

    def image(n):
        # Réutilise les images du site, à tour de rôle ; aucune image = placeholder
        return portraits[n % len(portraits)] if portraits else None

    def cle_image(prefixe, titre):
        """« heros » + « Sœur Ysolde » -> « heros-soeur-ysolde » (nom du fichier)."""
        return f"{prefixe}-{slug_de_fichier(titre)}"

    def illustration(cle, repli):
        """L'image de démo de cette clé, sinon l'image de secours."""
        return demo.get(cle, repli)

    def article(intro, gravure, position, ornement="lettrine"):
        """Un corps d'article de démo : de quoi voir chaque bloc du StreamField."""
        blocs = [('enluminure', {'ornement': ornement, 'texte': (
            "<p>Il est dit, dans les registres de la Guilde des Copistes, que nul ne "
            "connaît le premier mot de cette histoire. On sait seulement qu'il fut "
            "écrit à l'encre de brume, et qu'il s'efface quand on le lit à voix haute.</p>")}),
            ('section', {'titre': "Ce qu'on en sait", 'texte': (
                f"<p>{intro} Les érudits ne sont d'accord sur rien, sauf sur le fait "
                "qu'il vaut mieux ne pas en parler la nuit.</p>")})]
        if gravure:
            blocs.append(('image', {'image': gravure, 'caption': "Gravure d'un érudit anonyme",
                                    'alt_text': "", 'position': position}))
        blocs += [
            ('section', {'titre': "Rumeurs", 'texte': (
                "<p>On raconte beaucoup de choses dans les tavernes de Port-Lanterne. "
                "La moitié sont fausses, l'autre moitié aussi, mais pas de la même façon.</p>"
                "<h3>Ce qu'en disent les anciens</h3><p>Rien. Ils dorment.</p>")}),
            ('separateur', None),
            ('paragraph', "<p><em>Note du MJ : à compléter avant la prochaine séance.</em></p>"),
        ]
        return blocs

    def publier(parent, page, tags=(), categorie=None):
        if categorie:
            page.categorie = cats[categorie]
        parent.add_child(instance=page)
        for tag in tags:
            page.tags.add(tag)
        page.save_revision().publish()
        return page

    # Lieux et Lore : dans l'encyclopédie
    lieux = {}
    for n, (titre, (cat, intro, tags, epingle)) in enumerate(LIEUX.items()):
        lieux[titre] = publier(encyclopedie, LieuPage(
            title=titre, intro=f"<p>{intro}</p>", epinglee=epingle,
            main_image=illustration(cle_image("lieu", titre), image(n) if n % 2 else None),
        ), tags, cat)
    for n, (titre, (cat, intro, tags, epingle)) in enumerate(LORE.items()):
        gravure = gravures[n % len(gravures)] if gravures else image(n + 1)
        publier(encyclopedie, LorePage(
            caracteristiques=STATS_DU_LORE.get(titre, []),
            title=titre, intro=f"<p>{intro}</p>", epinglee=epingle,
            main_image=illustration(cle_image("lore", titre), image(n) if n % 3 else None),
            body=article(intro, gravure, 'droite' if n % 2 else 'gauche',
                         ornement=("lettrine", "marge", "cadre")[n % 3]),
        ), tags, cat)

    # La campagne et ses enfants
    # L'aide de jeu : un vrai fichier dans la bibliothèque « Documents »
    lettre = get_document_model()(title=AIDE_DE_JEU, collection=dossier("Aide de jeu"))
    lettre.file.save("lettre-du-messager.txt", ContentFile(TEXTE_AIDE_DE_JEU.encode("utf-8")), save=False)
    lettre.save()

    campagne = index.add_child(instance=CampagnePage(
        body=[
            ('section', {'titre': "Aides de jeu", 'texte': "<p>Ce que les joueurs ont trouvé en chemin.</p>"}),
            ('document', {'document': lettre, 'titre': "",
                          'description': "Trouvée dans la sacoche d'un messager, au bord de la route du nord."}),
        ],
        title=CAMPAGNE, subtitle="Campagne de démonstration", status='en_cours',
        card_description="Le brouillard est tombé sur Ardenn. Les routes bougent, les lanternes regardent.",
        synopsis="<p>Le brouillard est tombé sur Ardenn, et avec lui les vieilles légendes.</p>",
        banner_image=illustration("banniere", next((i for i in images if i.width >= i.height), None)),
    ))
    campagne.save_revision().publish()

    for titre, texte in PRESENCES.items():
        PresenceEnCampagne.objects.create(fiche=LorePage.objects.get(title=titre), campagne=campagne, texte=texte)

    carte_du_site = next((i for i in images if "carte" in i.title.lower()), None)
    cartes = {
        "Carte d'Ardenn": CartePage(title="Carte d'Ardenn", is_main_map=True,
                                     main_image=illustration("carte-ardenn", carte_du_site),
                                     intro="<p>La carte du continent, telle qu'on la dessinait avant le Grand Brouillard.</p>"),
        "Carte du Val Gris": CartePage(title="Carte du Val Gris",
                                       # Sans le fichier carte-val-gris : image d'attente (placeholder)
                                       main_image=illustration("carte-val-gris", None),
                                       intro="<p>Le Val Gris, tel que l'ont dessiné ceux qui en sont revenus.</p>"),
    }
    for carte in cartes.values():
        campagne.add_child(instance=carte)
    for nom_carte, nom_lieu, position, epoque in APPARITIONS:
        est_zone = isinstance(position, list)
        x, y = position if position and not est_zone else (None, None)
        champs = dict(forme=position if est_zone else None, coord_x=x, coord_y=y, a_cette_epoque=epoque)
        champs.update(STYLES_DE_ZONES.get((nom_carte, nom_lieu), {}))
        Apparition.objects.create(carte=cartes[nom_carte], lieu=lieux[nom_lieu], **champs)
    for carte in cartes.values():
        # La publication range les lieux (CartePage.ranger_les_lieux)
        carte.save_revision().publish()

    chrono = campagne.add_child(instance=ChronologiePage(
        title="Chroniques des Brumes", systeme_datation="Années après le Grand Brouillard",
        intro="<p>Les dates négatives sont antérieures au Grand Brouillard.</p>",
    ))
    chrono.save_revision().publish()
    for n, (titre, (cat, ordre, date, lieu, intro, tags)) in enumerate(EVENEMENTS.items()):
        publier(chrono, EvenementPage(
            title=titre, date_ordre=ordre, date_affichage=date, lieu=lieux[lieu], intro=f"<p>{intro}</p>",
            main_image=illustration(cle_image("evenement", titre), image(n) if n % 2 == 0 else None),
        ), tags, cat)

    for n, (titre, (cat, joueur, origine, intro, tags, epingle, joue_par, parti)) in enumerate(HEROS.items()):
        publier(campagne, HeroPage(
            caracteristiques=STATS_DES_HEROS.get(titre, []),
            title=titre, joueur_nom=joueur, lieu_origine=lieux[origine], epinglee=epingle,
            joue_par=joue_par, a_quitte_le_groupe=parti,
            intro=f"<p>{intro}</p>", main_image=illustration(cle_image("heros", titre), image(n)),
            joueur_bio="<p>Joue depuis trois campagnes, apporte toujours les chips.</p>" if joueur else "",
        ), tags, cat)

    return len(demo)


def _creer_categories():
    """Crée l'arbre s'il manque des branches ; réutilise ce qui existe déjà (ex. « Lieu »)."""
    cats = {}
    for ordre, (nom, parent, couleur, defaut) in enumerate(CATEGORIES):
        categorie = (Categorie.objects.filter(par_defaut_pour=defaut).first() if defaut else None) \
            or Categorie.objects.filter(nom=nom, parent=cats.get(parent)).first()
        if categorie is None:
            categorie = Categorie(nom=nom, parent=cats.get(parent))
        categorie.ordre = ordre
        categorie.couleur = categorie.couleur or couleur
        categorie.par_defaut_pour = defaut or categorie.par_defaut_pour
        categorie.parent = cats.get(parent)
        categorie.save()
        cats[nom] = categorie
    return cats


def _creer_familles():
    for nom, (couleur, ordre, tags) in FAMILLES.items():
        famille, _ = FamilleDeTags.objects.get_or_create(nom=nom, defaults={'couleur': couleur, 'ordre': ordre})
        for nom_tag in tags:
            tag = Tag.objects.filter(name__iexact=nom_tag).first() or Tag.objects.create(name=nom_tag)
            if not tag.familles.exclude(pk=famille.pk).exists():  # un tag = une famille
                famille.tags.add(tag)


# ------------------------------------------------------------------- suppression
def supprimer_demo():
    """Retire tout le contenu de démo et renvoie une phrase de compte rendu."""
    encyclopedie = EncyclopedieIndexPage.objects.first()
    compte = 0
    with transaction.atomic():
        campagne = CampagnePage.objects.filter(title=CAMPAGNE).first()
        if campagne:
            compte += campagne.get_descendants(inclusive=True).count()
            campagne.delete()  # supprime aussi cartes, apparitions, chronologie, héros
        fiches = []
        if encyclopedie:
            fiches = list(LieuPage.objects.child_of(encyclopedie).filter(title__in=LIEUX)) \
                + list(LorePage.objects.child_of(encyclopedie).filter(title__in=LORE))
        for page in fiches:
            page.delete()
        compte += len(fiches)
        FamilleDeTags.objects.filter(nom__in=FAMILLES).delete()
        # Wagtail efface aussi le fichier du disque quand on supprime le document / l'image
        get_document_model().objects.filter(title=AIDE_DE_JEU).delete()
        images = list(Image.objects.filter(tags__name=TAG_IMAGES))
        for image in images:
            image.delete()

        # Les tags créés par la démo qui ne servent plus à AUCUNE fiche
        # (« pouet » et les tags du MJ, encore utilisés, sont gardés).
        noms = {tag for tags in FAMILLES.values() for tag in tags[2]}
        tags_inutilises = Tag.objects.filter(
            name__in=noms,
            campagnes_heropagetag_items__isnull=True,
            campagnes_lieupagetag_items__isnull=True,
            campagnes_evenementpagetag_items__isnull=True,
            encyclopedie_lorepagetag_items__isnull=True,
        )
        nb_tags = tags_inutilises.count()
        tags_inutilises.delete()
    return (f"Démo retirée : {compte} pages, {len(images)} image(s) et {nb_tags} tags de démo "
            "supprimés (les catégories et les dossiers sont conservés).")
