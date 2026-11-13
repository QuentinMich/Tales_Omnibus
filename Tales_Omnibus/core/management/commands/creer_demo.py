"""
Crée une CAMPAGNE DE DÉMONSTRATION pour visualiser toutes les fonctionnalités :
    ../env/Scripts/python.exe manage.py creer_demo
    ../env/Scripts/python.exe manage.py creer_demo --supprimer

Contenu : une campagne « Les Brumes d'Ardenn » (2 cartes, une chronologie,
3 héros), des lieux et des fiches Lore dans l'encyclopédie, un arbre de
catégories, des familles de tags, des tags, des fiches épinglées, un lieu
présent sur deux cartes…

Tout le contenu est DÉCLARÉ ci-dessous : c'est ce qui permet à --supprimer de
retirer exactement ce que la démo a créé, sans toucher aux vraies pages.
Les catégories, elles, sont conservées : ce sont des rangements réutilisables.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from taggit.models import Tag
from wagtail.images.models import Image

from campagnes.models import (
    Apparition, CampagnePage, CampagnesIndexPage, CartePage, ChronologiePage, EvenementPage, HeroPage, LieuPage,
)
from core.models import Categorie
from encyclopedie.models import EncyclopedieIndexPage, FamilleDeTags, LorePage

CAMPAGNE = "Les Brumes d'Ardenn"

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
}

# --- Apparitions : (carte, lieu, x, y, à cette époque) ------------------------
APPARITIONS = [
    ("Carte d'Ardenn", "Ardenn", 50, 50, ""),
    ("Carte d'Ardenn", "Port-Lanterne", 30, 62, ""),
    ("Carte d'Ardenn", "Fort-Sombre", 66, 24, "Encore debout, tenu par l'Ordre du Corbeau."),
    ("Carte d'Ardenn", "Hameau des Saules", 44, 80, ""),
    ("Carte du Val Gris", "Royaume du Val Gris", 50, 45, "Caché par le brouillard : aucune carte du monde ne le montre."),
    ("Carte du Val Gris", "Port-Lanterne", 18, 70, "Reconstruit après le Grand Brouillard."),
    ("Carte du Val Gris", "Fort-Sombre", None, None, ""),  # ajouté à la carte mais pas encore placé
]

# --- Fiches Lore : titre -> (catégorie, intro, tags, épinglé) -----------------
LORE = {
    "Vaël, déesse des Brumes": ("Déité majeure", "Elle tisse le brouillard et décide qui s'y perd.", ["prophétie", "esprit"], True),
    "Kroth le Petit": ("Déité mineure", "Dieu des clés perdues. Il les garde, évidemment.", ["runes"], False),
    "L'Ordre du Corbeau": ("Faction", "Des chevaliers qui ne parlent qu'aux oiseaux. Les oiseaux, eux, parlent beaucoup.", ["Ordre du Corbeau"], False),
    "Le Marchand Borgne": ("PNJ", "Il vend de tout, surtout ce qu'il n'a pas. Son œil manquant est à vendre aussi.", ["Guilde des Brumes", "pouet"], False),
    "Le Dragon de Suie": ("Créature", "Un dragon fait de fumée. Il éternue des incendies.", ["dragon", "malédiction"], True),
    "L'Épée sans Nom": ("Objet", "Une épée qui refuse qu'on la nomme. Le dernier qui a essayé s'appelle désormais « Machin ».", ["runes", "malédiction"], False),
    "La Légende du Lac Gris": ("Légende", "Au fond du lac dort un royaume entier. Il ronfle.", ["esprit", "prophétie"], False),
    "Notes du MJ": (None, "Une fiche sans catégorie : elle tombe dans la catégorie par défaut du Lore.", ["pouet"], False),
}

# --- Chronologie : titre -> (catégorie, date_ordre, date affichée, lieu, intro, tags)
EVENEMENTS = {
    "La Nuit des Cendres": ("Bataille", -12, "An -12, nuit du solstice", "Fort-Sombre",
                            "Le Dragon de Suie attaque le fort. Personne ne gagne, tout le monde tousse.", ["dragon", "Ordre du Corbeau"]),
    "Le Grand Brouillard": ("Catastrophe", 0, "An 0", "Ardenn",
                            "La brume recouvre le continent. Le calendrier repart de zéro, par commodité.", ["prophétie"]),
    "Le Bal des Lanternes": ("Fête", 3, "An 3, premier jour du printemps", "Port-Lanterne",
                             "Une fête où chacun danse avec une lanterne. Certaines lanternes dansent mieux.", ["esprit", "pouet"]),
    "Le Pacte du Corbeau": (None, 7, "An 7", "Fort-Sombre",
                            "Sans catégorie : il apparaît sous « Événement » par défaut.", ["Ordre du Corbeau", "runes"]),
}

# --- Héros : titre -> (catégorie, joueur, lieu d'origine, intro, tags, épinglé)
HEROS = {
    "Maëlis Ventcourt": ("Héros", "Joueuse A", "Port-Lanterne",
                         "Une cartographe qui dessine les routes avant qu'elles bougent.", ["runes", "prophétie"], True),
    "Brann le Rouquin": ("Héros", "Joueur B", "Hameau des Saules",
                         "Un bûcheron convaincu que son hache est hantée. Elle l'est.", ["esprit", "pouet"], False),
    "Sœur Ysolde": ("PNJ", "MJ", "Fort-Sombre",
                    "Un PNJ rangé comme fiche Héros : sa catégorie le classe quand même en PNJ.", ["Ordre du Corbeau"], False),
}


class Command(BaseCommand):
    help = "Crée (ou supprime avec --supprimer) une campagne de démonstration."

    def add_arguments(self, parser):
        parser.add_argument('--supprimer', action='store_true', help="Retire tout le contenu de démo.")

    def handle(self, *args, **options):
        index = CampagnesIndexPage.objects.first()
        encyclopedie = EncyclopedieIndexPage.objects.first()
        if not index or not encyclopedie:
            raise CommandError("Il faut d'abord les pages « Campagnes » et « Encyclopédie ».")

        if options['supprimer']:
            self.supprimer(encyclopedie)
            return
        if CampagnePage.objects.filter(title=CAMPAGNE).exists():
            raise CommandError("La démo existe déjà. Lance d'abord : manage.py creer_demo --supprimer")

        # transaction.atomic : si quoi que ce soit plante, RIEN n'est créé
        # (pas de démo à moitié construite dans la base).
        with transaction.atomic():
            self.creer(index, encyclopedie)
        self.stdout.write(self.style.SUCCESS("Démo créée. Pour la retirer : manage.py creer_demo --supprimer"))

    # ------------------------------------------------------------------ création
    def creer(self, index, encyclopedie):
        cats = self.creer_categories()
        self.creer_familles()
        images = list(Image.objects.all())
        # Portraits : images en hauteur, sauf la carte (elle sert aux cartes !)
        portraits = [i for i in images if i.height > i.width and "carte" not in i.title.lower()] or images

        def image(n):
            # Réutilise les images du site, à tour de rôle ; aucune image = placeholder
            return portraits[n % len(portraits)] if portraits else None

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
                title=titre, intro=f"<p>{intro}</p>", epinglee=epingle, main_image=image(n) if n % 2 else None,
            ), tags, cat)
        for n, (titre, (cat, intro, tags, epingle)) in enumerate(LORE.items()):
            publier(encyclopedie, LorePage(
                title=titre, intro=f"<p>{intro}</p>", epinglee=epingle, main_image=image(n) if n % 3 else None,
                body=[('paragraph', f"<h2>Ce qu'on en sait</h2><p>{intro} Les érudits ne sont d'accord sur rien, "
                                    f"sauf sur le fait qu'il vaut mieux ne pas en parler la nuit.</p>")],
            ), tags, cat)

        # La campagne et ses enfants
        campagne = index.add_child(instance=CampagnePage(
            title=CAMPAGNE, subtitle="Campagne de démonstration", status='en_cours',
            card_description="Une campagne factice pour tester toutes les fonctionnalités du site.",
            synopsis="<p>Le brouillard est tombé sur Ardenn, et avec lui les vieilles légendes.</p>",
            banner_image=next((i for i in images if i.width >= i.height), None),
        ))
        campagne.save_revision().publish()

        carte_image = next((i for i in images if "carte" in i.title.lower()), None)
        cartes = {
            "Carte d'Ardenn": CartePage(title="Carte d'Ardenn", main_image=carte_image, is_main_map=True,
                                         intro="<p>La carte du continent, telle qu'on la dessinait avant le Grand Brouillard.</p>"),
            "Carte du Val Gris": CartePage(title="Carte du Val Gris",
                                           intro="<p>Une carte régionale (sans image : on voit le placeholder).</p>"),
        }
        for carte in cartes.values():
            campagne.add_child(instance=carte)
        for nom_carte, nom_lieu, x, y, epoque in APPARITIONS:
            Apparition.objects.create(carte=cartes[nom_carte], lieu=lieux[nom_lieu],
                                      coord_x=x, coord_y=y, a_cette_epoque=epoque)
        for carte in cartes.values():
            carte.save_revision().publish()

        chrono = campagne.add_child(instance=ChronologiePage(
            title="Chroniques des Brumes", systeme_datation="Années après le Grand Brouillard",
            intro="<p>Les dates négatives sont antérieures au Grand Brouillard.</p>",
        ))
        chrono.save_revision().publish()
        for n, (titre, (cat, ordre, date, lieu, intro, tags)) in enumerate(EVENEMENTS.items()):
            publier(chrono, EvenementPage(
                title=titre, date_ordre=ordre, date_affichage=date, lieu=lieux[lieu],
                intro=f"<p>{intro}</p>", main_image=image(n) if n % 2 == 0 else None,
            ), tags, cat)

        for n, (titre, (cat, joueur, origine, intro, tags, epingle)) in enumerate(HEROS.items()):
            publier(campagne, HeroPage(
                title=titre, joueur_nom=joueur, lieu_origine=lieux[origine], epinglee=epingle,
                intro=f"<p>{intro}</p>", main_image=image(n),
                joueur_bio="<p>Joue depuis trois campagnes, apporte toujours les chips.</p>",
            ), tags, cat)

    def creer_categories(self):
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

    def creer_familles(self):
        for nom, (couleur, ordre, tags) in FAMILLES.items():
            famille, _ = FamilleDeTags.objects.get_or_create(nom=nom, defaults={'couleur': couleur, 'ordre': ordre})
            for nom_tag in tags:
                tag = Tag.objects.filter(name__iexact=nom_tag).first() or Tag.objects.create(name=nom_tag)
                if not tag.familles.exclude(pk=famille.pk).exists():  # un tag = une famille
                    famille.tags.add(tag)

    # --------------------------------------------------------------- suppression
    def supprimer(self, encyclopedie):
        compte = 0
        campagne = CampagnePage.objects.filter(title=CAMPAGNE).first()
        if campagne:
            compte += campagne.get_descendants(inclusive=True).count()
            campagne.delete()  # supprime aussi cartes, apparitions, chronologie, héros
        fiches = list(LieuPage.objects.child_of(encyclopedie).filter(title__in=LIEUX)) \
            + list(LorePage.objects.child_of(encyclopedie).filter(title__in=LORE))
        for page in fiches:
            page.delete()
        compte += len(fiches)
        FamilleDeTags.objects.filter(nom__in=FAMILLES).delete()

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
        self.stdout.write(self.style.SUCCESS(
            f"{compte} pages et {nb_tags} tags de démo supprimés (les catégories sont conservées)."
        ))
