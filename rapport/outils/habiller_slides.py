"""Habille les slides de la soutenance aux couleurs de Tales Omnibus.

Partie 1 : reprend le contenu, les images et les notes de « Slides Tales
Omnibus.pptx » (le fichier d'origine n'est pas modifié) et les remet en page.
Partie 2 : le cas pratique SEO / accessibilité, construit d'après
plan_partie2.md. Les captures à venir (Lighthouse…) sont des CADRES VIDES en
pointillés, nommés « Capture à venir : … » dans le volet Sélection de
PowerPoint : clic droit > Modifier l'image n'existe pas sur un rectangle, donc
on colle la capture, on la pose dessus, puis on supprime le cadre.

Style : cuir sombre et or (le thème Grimoire et le logo doré), titres en
Palatino Linotype, texte en Calibri, code en Consolas : les trois sont livrés
avec Windows et Office, rien ne change sur l'ordinateur de la salle.
Motif : les COINS DORÉS des panneaux du site, sur chaque image et chaque carte.

Lancer depuis la racine du dépôt :
    python rapport/outils/habiller_slides.py
(dépendances : python-pptx, pymupdf, pillow ; outils de mise en page, pas
dans requirements.txt)
"""
import io
import random
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFilter
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt
from lxml import etree

RACINE = Path(__file__).resolve().parents[2]
SLIDES = RACINE / "rapport" / "slides"
CAPTURES = RACINE / "rapport" / "captures"
IMG_SITE = RACINE / "Tales_Omnibus" / "Tales_Omnibus" / "static" / "img"
SOURCE = SLIDES / "Slides Tales Omnibus.pptx"
SORTIE_1 = SLIDES / "Soutenance partie 1 - Présentation.pptx"
SORTIE_2 = SLIDES / "Soutenance partie 2 - SEO et accessibilité.pptx"
CAPTURES = SLIDES / "captures_lighthouse"
CAPTURE_PUBLIER = SLIDES / "captures" / "sudo_publier.png"

# Scores Lighthouse (accessibilité ordinateur avant / après, mobile avant /
# après, SEO). None = pas encore mesuré : la case affiche « … ».
PAGES_AUDITEES = ["accueil", "campagne", "lore", "encyclopedie"]
NOMS_DES_PAGES = {"accueil": "Accueil", "campagne": "Campagne", "lore": "Fiche de lore",
                  "encyclopedie": "Encyclopédie"}
SCORES = {
    "accueil": (100, 100, 96, 100, 100),
    "campagne": (100, 100, 96, 100, 100),
    "lore": (96, 100, 92, 100, 100),
    "encyclopedie": (100, 100, 96, 100, 100),
}


def grille_captures(slide, moment, x, y, w, h, largeur_libelle=1.55):
    """Les 8 captures d'un moment (avant / apres) : 4 pages × ordinateur, mobile."""
    ecart = 0.15
    larg = (w - largeur_libelle - ecart) / 2
    haut = (h - 0.45) / len(PAGES_AUDITEES) - 0.1
    x1 = x + largeur_libelle
    x2 = x1 + larg + ecart
    texte(slide, x1, y - 0.05, larg, 0.35, "Ordinateur", taille=14, couleur=OR_CLAIR, gras=True, align=PP_ALIGN.CENTER)
    texte(slide, x2, y - 0.05, larg, 0.35, "Mobile", taille=14, couleur=OR_CLAIR, gras=True, align=PP_ALIGN.CENTER)
    for k, page in enumerate(PAGES_AUDITEES):
        yy = y + 0.4 + k * (haut + 0.1)
        texte(slide, x - 0.2, yy, largeur_libelle - 0.1, haut, NOMS_DES_PAGES[page], taille=14, couleur=TEXTE,
              align=PP_ALIGN.RIGHT, ancre=MSO_ANCHOR.MIDDLE)
        image(slide, capture(f"{moment}_{page}_ordi", 200), x1, yy, larg, haut)
        image(slide, capture(f"{moment}_{page}_mobile", 200), x2, yy, larg, haut)


def capture(nom, hauteur_max=None):
    """Une capture Lighthouse ; hauteur_max (px) n'en garde que le haut."""
    chemin = CAPTURES / f"{nom}.png"
    if hauteur_max is None:
        return chemin
    im = Image.open(chemin)
    if im.height <= hauteur_max:
        return chemin
    tampon = io.BytesIO()
    im.crop((0, 0, im.width, hauteur_max)).save(tampon, format="PNG")
    return tampon.getvalue()

# --- Palette (cuir et or) ----------------------------------------------------
FOND = "1E1712"
SURFACE = "2A2119"
SURFACE_2 = "33281E"
BORD = "5C4A30"
OR = "C29A3E"        # le doré du logo et de l'icône d'onglet
OR_CLAIR = "E2C27A"
TEXTE = "EEE4CF"
DOUX = "B3A385"
VERT = "8FB573"

TITRE = "Palatino Linotype"
CORPS = "Calibri"
CODE = "Consolas"

L, H = 13.333, 7.5


def rgb(hexa):
    return RGBColor.from_string(hexa)


# --- Images générées : fond, logo, bannière --------------------------------
def fond_cuir(chemin):
    """Cuir sombre : vignettage + grain léger (PIL, 1920×1080)."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), "#" + FOND)
    lueur = Image.new("L", (w, h), 0)
    ImageDraw.Draw(lueur).ellipse((-200, -350, w + 200, h + 250), fill=255)
    lueur = lueur.filter(ImageFilter.GaussianBlur(260))
    clair = Image.new("RGB", (w, h), "#2C2219")
    sombre = Image.new("RGB", (w, h), "#0F0B08")
    img = Image.composite(clair, sombre, lueur)
    random.seed(7)
    grain = Image.effect_noise((w, h), 18).convert("L")
    img = Image.blend(img, Image.merge("RGB", (grain,) * 3), 0.035)
    img.save(chemin, quality=88)


def svg_en_png(svg, chemin, hauteur_px, couleur="#" + OR):
    texte = svg.read_text(encoding="utf-8").replace('fill="#000"', f'fill="{couleur}"')
    doc = pymupdf.open(stream=texte.encode(), filetype="svg")
    page = doc[0]
    zoom = hauteur_px / page.rect.height
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True)
    pix.save(chemin)
    return pix.width / pix.height


# --- Petits outils de mise en page -----------------------------------------
def poser_fond(prs, image):
    """Fond de la mise en page « vide » : toutes les slides en héritent."""
    layout = prs.slide_layouts[6]
    _, rid = layout.part.get_or_add_image_part(str(image))
    csld = layout._element.find(qn("p:cSld"))
    ancien = csld.find(qn("p:bg"))
    if ancien is not None:
        csld.remove(ancien)
    bg = etree.SubElement(csld, qn("p:bg"))
    csld.remove(bg)
    csld.insert(0, bg)
    bgpr = etree.SubElement(bg, qn("p:bgPr"))
    fill = etree.SubElement(bgpr, qn("a:blipFill"), dpi="0", rotWithShape="1")
    blip = etree.SubElement(fill, qn("a:blip"))
    blip.set(qn("r:embed"), rid)
    etree.SubElement(etree.SubElement(fill, qn("a:stretch")), qn("a:fillRect"))
    etree.SubElement(bgpr, qn("a:effectLst"))
    return layout


def rect(slide, x, y, w, h, fond=None, bord=None, epaisseur=0.75, forme=MSO_SHAPE.RECTANGLE, nom=None):
    s = slide.shapes.add_shape(forme, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    if fond:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fond)
    else:
        s.fill.background()
    if bord:
        s.line.color.rgb = rgb(bord)
        s.line.width = Pt(epaisseur)
    else:
        s.line.fill.background()
    if nom:
        s.name = nom
    return s


def texte(slide, x, y, w, h, contenu, taille=18, couleur=TEXTE, police=CORPS, gras=False,
          italique=False, align=PP_ALIGN.LEFT, ancre=MSO_ANCHOR.TOP, interligne=None, nom=None):
    """contenu : une chaîne (\\n = nouveau paragraphe) ou une liste de
    paragraphes, chacun une chaîne ou une liste de runs (texte, {options})."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if nom:
        tb.name = nom
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = ancre
    paragraphes = contenu.split("\n") if isinstance(contenu, str) else contenu
    for i, para in enumerate(paragraphes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if interligne:
            p.line_spacing = interligne
        runs = [(para, {})] if isinstance(para, str) else para
        for txt, opt in runs:
            r = p.add_run()
            r.text = txt
            f = r.font
            f.name = opt.get("police", police)
            f.size = Pt(opt.get("taille", taille))
            f.bold = opt.get("gras", gras)
            f.italic = opt.get("italique", italique)
            f.color.rgb = rgb(opt.get("couleur", couleur))
    return tb


def puces(slide, x, y, w, h, lignes, taille=17, couleur=TEXTE, espace=8, puce="◆"):
    """Liste à puces (vraies puces PowerPoint, losange doré)."""
    tb = texte(slide, x, y, w, h, lignes, taille=taille, couleur=couleur)
    for p in tb.text_frame.paragraphs:
        p.space_after = Pt(espace)
        ppr = p._p.get_or_add_pPr()
        ppr.set("marL", str(Inches(0.3)))
        ppr.set("indent", str(-Inches(0.3)))
        for tag in ("a:buClr", "a:buSzPct", "a:buFont", "a:buChar"):
            ancien = ppr.find(qn(tag))
            if ancien is not None:
                ppr.remove(ancien)
        clr = etree.SubElement(ppr, qn("a:buClr"))
        etree.SubElement(clr, qn("a:srgbClr"), val=OR)
        etree.SubElement(ppr, qn("a:buSzPct"), val="70000")
        etree.SubElement(ppr, qn("a:buFont"), typeface="Segoe UI Symbol")
        etree.SubElement(ppr, qn("a:buChar"), char=puce)
    return tb


def coins(slide, x, y, w, h, taille=0.22, ep=0.035, couleur=OR, ecart=0.07):
    """Les coins dorés des panneaux du site, posés autour d'un cadre."""
    x0, y0, x1, y1 = x - ecart, y - ecart, x + w + ecart, y + h + ecart
    for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        hx = cx if sx > 0 else cx - taille
        vy = cy if sy > 0 else cy - taille
        rect(slide, hx, cy if sy > 0 else cy - ep, taille, ep, fond=couleur, nom="Coin doré")
        rect(slide, cx if sx > 0 else cx - ep, vy, ep, taille, fond=couleur, nom="Coin doré")


def carte(slide, x, y, w, h, fond=SURFACE, avec_coins=True):
    rect(slide, x, y, w, h, fond=fond, bord=BORD, nom="Carte")
    if avec_coins:
        coins(slide, x, y, w, h, taille=0.18, ep=0.03, ecart=0.05)


def image(slide, source, x, y, w, h, cadre=True, align="centre", nom=None, fond=None, marge=0.0):
    """Image contenue dans la boîte (jamais déformée), filet doré + coins."""
    blob = source.read_bytes() if isinstance(source, Path) else source
    iw, ih = Image.open(io.BytesIO(blob)).size
    if iw / ih > w / h:
        rw, rh = w, w * ih / iw
    else:
        rw, rh = h * iw / ih, h
    rx = x + (w - rw) / 2 if align == "centre" else (x if align == "gauche" else x + w - rw)
    ry = y + (h - rh) / 2
    if fond:
        # Fond clair SOUS une image transparente (croquis au trait noir)
        rect(slide, rx - marge, ry - marge, rw + 2 * marge, rh + 2 * marge, fond=fond,
             bord=BORD if cadre else None, nom="Fond de l'image")
    pic = slide.shapes.add_picture(io.BytesIO(blob), Inches(rx), Inches(ry), Inches(rw), Inches(rh))
    if nom:
        pic.name = nom
    if cadre and fond:
        coins(slide, rx - marge, ry - marge, rw + 2 * marge, rh + 2 * marge)
    elif cadre:
        pic.line.color.rgb = rgb(BORD)
        pic.line.width = Pt(1)
        coins(slide, rx, ry, rw, rh)
    return rx, ry, rw, rh


def emplacement(slide, x, y, w, h, libelle, detail=""):
    """Cadre VIDE pour une capture à venir (pointillés + légende)."""
    s = rect(slide, x, y, w, h, fond=SURFACE, bord=OR, epaisseur=1.25, nom=f"Capture à venir : {libelle}")
    s.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "Capture à venir"
    r.font.size, r.font.name, r.font.color.rgb, r.font.italic = Pt(12), CORPS, rgb(DOUX), True
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r = p2.add_run()
    r.text = libelle
    r.font.size, r.font.name, r.font.color.rgb, r.font.bold = Pt(15), CORPS, rgb(OR_CLAIR), True
    if detail:
        p3 = tf.add_paragraph()
        p3.alignment = PP_ALIGN.CENTER
        r = p3.add_run()
        r.text = detail
        r.font.size, r.font.name, r.font.color.rgb = Pt(11), CORPS, rgb(DOUX)
    coins(slide, x, y, w, h)
    return s


def code(slide, x, y, w, h, lignes, taille=13, legende=None):
    """Bloc de code : fond plus sombre, Consolas, légende (nom du fichier)."""
    carte(slide, x, y, w, h, fond="15100C")
    haut = y + 0.15
    if legende:
        texte(slide, x + 0.2, haut, w - 0.4, 0.3, legende, taille=11, couleur=OR, italique=True)
        haut += 0.35
    texte(slide, x + 0.2, haut, w - 0.4, h - (haut - y) - 0.1, lignes, taille=taille,
          couleur="D9CFB8", police=CODE, interligne=1.05)


def pastille(slide, x, y, w, h, contenu, taille=15, fond=SURFACE_2, couleur=TEXTE, police=CORPS, gras=False):
    s = rect(slide, x, y, w, h, fond=fond, bord=OR, forme=MSO_SHAPE.ROUNDED_RECTANGLE, nom="Pastille")
    s.adjustments[0] = 0.5
    tf = s.text_frame
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = contenu
    r.font.size, r.font.name, r.font.color.rgb, r.font.bold = Pt(taille), police, rgb(couleur), gras
    return s


def fleche(slide, x, y, w=0.45, h=0.32, couleur=OR):
    rect(slide, x, y, w, h, fond=couleur, forme=MSO_SHAPE.RIGHT_ARROW, nom="Flèche")


def numero(slide, x, y, chiffre, d=0.62, taille=20):
    """Médaillon doré (chiffre romain)."""
    s = rect(slide, x, y, d, d, fond=SURFACE_2, bord=OR, epaisseur=1.5, forme=MSO_SHAPE.OVAL, nom="Médaillon")
    tf = s.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = chiffre
    r.font.size, r.font.name, r.font.color.rgb, r.font.bold = Pt(taille), TITRE, rgb(OR_CLAIR), True


class Deck:
    def __init__(self, sortie, pied):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(L), Inches(H)
        self.layout = poser_fond(self.prs, FOND_IMG)
        self.sortie = sortie
        self.pied = pied

    def slide(self, titre=None, sous_titre=None, notes=None, pied=True):
        s = self.prs.slides.add_slide(self.layout)
        if titre:
            texte(s, 0.7, 0.38, 10.6, 0.75, titre, taille=34, couleur=OR_CLAIR, police=TITRE,
                  ancre=MSO_ANCHOR.BOTTOM, nom="Titre")
            # Filet doré + losange : la frise des titres du Grimoire
            rect(s, 0.7, 1.24, 2.4, 0.025, fond=OR, nom="Filet")
            losange = rect(s, 3.08, 1.185, 0.13, 0.13, fond=OR, forme=MSO_SHAPE.DIAMOND, nom="Filet")
            if sous_titre:
                texte(s, 3.45, 1.08, 8.5, 0.4, sous_titre, taille=16, couleur=DOUX, italique=True,
                      ancre=MSO_ANCHOR.MIDDLE, nom="Sous-titre")
        if pied:
            s.shapes.add_picture(str(LOGO_IMG), Inches(12.05), Inches(0.42), height=Inches(0.62)).name = "Logo"
            numero_slide = len(self.prs.slides)
            texte(s, 0.7, 7.0, 8, 0.3, self.pied, taille=10, couleur="8A7B62", nom="Pied de page")
            texte(s, 11.6, 7.0, 1.05, 0.3, str(numero_slide), taille=10, couleur="8A7B62",
                  align=PP_ALIGN.RIGHT, nom="Numéro")
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    def couverture(self, sur_titre, sous_titre, ligne_bas, notes=None):
        s = self.slide(pied=False, notes=notes)
        # Double cadre doré, comme une reliure
        rect(s, 0.3, 0.3, L - 0.6, H - 0.6, bord=OR, epaisseur=1.5, nom="Reliure")
        rect(s, 0.42, 0.42, L - 0.84, H - 0.84, bord=BORD, epaisseur=0.75, nom="Reliure")
        coins(s, 0.3, 0.3, L - 0.6, H - 0.6, taille=0.5, ep=0.06, ecart=0)
        if sur_titre:
            texte(s, 1, 0.8, L - 2, 0.4, sur_titre, taille=15, couleur=DOUX, align=PP_ALIGN.CENTER,
                  italique=True)
        hb = 3.3
        wb = hb * BANNIERE_RATIO
        s.shapes.add_picture(str(BANNIERE_IMG), Inches((L - wb) / 2), Inches(1.35), height=Inches(hb)).name = "Bannière"
        rect(s, L / 2 - 1.6, 4.95, 3.2, 0.025, fond=OR, nom="Filet")
        rect(s, L / 2 - 0.08, 4.895, 0.16, 0.16, fond=OR, forme=MSO_SHAPE.DIAMOND, nom="Filet")
        texte(s, 1.5, 5.2, L - 3, 0.9, sous_titre, taille=22, couleur=TEXTE, police=TITRE,
              align=PP_ALIGN.CENTER, interligne=1.1)
        texte(s, 1, 6.45, L - 2, 0.35, ligne_bas, taille=14, couleur=OR, align=PP_ALIGN.CENTER)
        return s

    def enregistrer(self):
        self.prs.save(self.sortie)
        print("écrit :", self.sortie.name, "-", len(self.prs.slides), "slides")


# --- Partie 1 : la présentation ---------------------------------------------
def images_de_la_source():
    """{(n° de slide, nom de forme): blob} + notes, depuis le deck d'origine."""
    src = Presentation(SOURCE)
    images, notes = {}, {}
    for i, s in enumerate(src.slides, 1):
        for sh in s.shapes:
            try:
                images[(i, sh.name)] = sh.image.blob
            except (AttributeError, ValueError):
                pass
        if s.has_notes_slide:
            notes[i] = s.notes_slide.notes_text_frame.text
    return images, notes


def partie_1():
    img, notes = images_de_la_source()
    d = Deck(SORTIE_1, "Tales Omnibus · Soutenance CMS · Quentin Michelet")

    # 1. Couverture
    d.couverture("Soutenance · Concepteur de sites CMS",
                 "Application de regroupement d’histoires et d’informations\nsur l’univers d’un maître du jeu et de son jeu de rôle",
                 "Quentin Michelet · Simplon Bordeaux", notes[1])

    # 2. Qui je suis
    s = d.slide(notes=notes[2])
    texte(s, 0.9, 1.6, 6, 1.0, "Quentin Michelet", taille=48, couleur=OR_CLAIR, police=TITRE)
    rect(s, 0.95, 2.75, 2.4, 0.025, fond=OR)
    texte(s, 0.9, 3.0, 5.5, 1.2, "Développeur\net maître du jeu", taille=28, couleur=TEXTE, police=TITRE,
          interligne=1.1)
    texte(s, 0.9, 5.55, 6, 0.5, [[("De mon besoin…  ", {}), ("au client type", {"couleur": OR_CLAIR, "gras": True}),
                                  ("  ➜", {"couleur": OR})]], taille=20, couleur=DOUX, italique=True)
    carte(s, 7.3, 1.45, 5.0, 2.45)
    image(s, img[(2, "Espace réservé du contenu 4")], 8.15, 1.8, 3.3, 0.8, cadre=False, fond="F4EEE2", marge=0.12)
    texte(s, 7.6, 2.95, 4.4, 0.8, [[("Formation", {"couleur": DOUX, "taille": 14})],
                                   [("Découverte Métier IA", {"gras": True, "taille": 20})]],
          align=PP_ALIGN.CENTER)
    carte(s, 7.3, 4.3, 5.0, 2.25)
    texte(s, 7.6, 4.5, 4.4, 1.9, [[("Tales", {"police": TITRE, "couleur": OR_CLAIR, "taille": 36})],
                                  [("Projet personnel", {"taille": 18})],
                                  [("4 ans de travail", {"taille": 18, "couleur": DOUX})]],
          align=PP_ALIGN.CENTER)

    # 3. Le maître du jeu (demandé par le formateur : dire ce que c'est)
    s = d.slide("Le maître du jeu", "Celui qui fait vivre l’histoire",
                notes="≈ 45 s\n- Le jeu de rôle : des joueurs incarnent chacun un personnage, autour d'une table ou en "
                      "ligne, et vivent ensemble une histoire.\n- Le MAÎTRE DU JEU (MJ) : il CRÉE le monde (lieux, peuples, "
                      "dieux, histoire), il RACONTE (décrit les scènes, joue tous les personnages non-joueurs, arbitre "
                      "les règles), et il se SOUVIENT de tout ce qui s'est passé.\n- Une campagne dure des mois, parfois "
                      "des années : des dizaines de séances, des centaines de personnages et de lieux.\n- LE PROBLÈME : "
                      "tout est éparpillé (carnets, Discord, vidéos). Un joueur oublie, un spectateur qui arrive en cours "
                      "est perdu.\n- Transition : « Il lui faut un endroit qui range tout. C'est Tales Omnibus. »")
    roles = [("I", "Il crée", "Un monde entier : lieux,\npeuples, dieux, histoire"),
             ("II", "Il raconte", "Décrit les scènes, joue\nles personnages, arbitre"),
             ("III", "Il se souvient", "Des mois, des années\nde séances")]
    for k, (n, nom, detail) in enumerate(roles):
        x = 0.8 + k * 3.95
        carte(s, x, 1.8, 3.75, 2.75)
        numero(s, x + 1.5, 2.0, n, d=0.75, taille=18 if len(n) < 3 else 15)
        texte(s, x + 0.2, 2.9, 3.35, 0.55, nom, taille=24, couleur=OR_CLAIR, police=TITRE, align=PP_ALIGN.CENTER)
        texte(s, x + 0.2, 3.5, 3.35, 0.9, detail, taille=15, couleur=DOUX, align=PP_ALIGN.CENTER, interligne=1.1)
    texte(s, 0.8, 4.95, 11.7, 0.5,
          [[("Le problème : ", {"couleur": OR_CLAIR, "gras": True}),
            ("tout est éparpillé, entre carnets, Discord et vidéos.", {})]],
          taille=19, align=PP_ALIGN.CENTER)
    pastille(s, 3.4, 5.7, 6.5, 0.7, "➜  Il lui faut un site qui range tout", taille=19,
             couleur=OR_CLAIR, police=TITRE)

    # 4. Le client type
    s = d.slide("Le client type",
                notes="≈ 1 min — C1, analyse du besoin\n- Le client type : un MJ, avec ou sans live, qui veut partager "
                      "son histoire.\n- Les 4 noms : des gens qui POURRAIENT utiliser mon site, des grosses productions "
                      "(Critical Role) aux petits créateurs (Onyrill).\n- 4 objectifs du cadrage :\n"
                      "  CENTRALISATION : toutes les informations, aujourd'hui dispersées partout, sur un seul site ;\n"
                      "  EXPLORATION : des pages qui donnent envie d'aller plus loin (encyclopédie, cartes, fiches reliées) ;\n"
                      "  AUTONOMIE : le MJ gère tout lui-même, sans coder ;\n"
                      "  RÉSEAU : Twitch, YouTube, Discord, contact, pour se faire connaître.\n"
                      "- Pourquoi un client type : je veux DISTRIBUER l'outil gratuitement → tout doit s'adapter "
                      "et s'installer clé en main.")
    carte(s, 0.8, 1.75, 5.6, 4.85)
    texte(s, 1.1, 1.95, 5.0, 0.6, "Maître du jeu", taille=30, couleur=OR_CLAIR, police=TITRE, align=PP_ALIGN.CENTER)
    texte(s, 1.1, 2.6, 5.0, 0.9, "Avec ou sans plateforme audiovisuelle\nPartager son histoire",
          taille=18, align=PP_ALIGN.CENTER, interligne=1.15)
    texte(s, 1.1, 3.65, 5.0, 0.4, "Ils pourraient l’utiliser :", taille=14, couleur=DOUX, italique=True,
          align=PP_ALIGN.CENTER)
    for k, nom in enumerate(["Critical Role", "Dimension 20", "La Bonne Auberge", "Onyrill"]):
        pastille(s, 1.25 + (k % 2) * 2.45, 4.15 + (k // 2) * 0.8, 2.25, 0.6, nom, taille=15)
    texte(s, 1.1, 5.85, 5.0, 0.4, [[("des grosses productions  ", {}), ("➜", {"couleur": OR}),
                                    ("  aux petits créateurs", {})]],
          taille=14, couleur=DOUX, italique=True, align=PP_ALIGN.CENTER)
    objectifs = [("I", "Centralisation", "Toutes les infos dispersées, sur un seul site"),
                 ("II", "Exploration", "Des pages qui donnent envie d’aller plus loin"),
                 ("III", "Autonomie", "Le MJ gère tout, sans coder"),
                 ("IV", "Réseau", "Twitch, YouTube, Discord, contact")]
    for k, (n, nom, detail) in enumerate(objectifs):
        y = 1.8 + k * 1.2
        numero(s, 7.0, y + 0.08, n, d=0.75, taille=18 if len(n) < 3 else 15)
        texte(s, 8.0, y, 4.5, 0.5, nom, taille=24, couleur=OR_CLAIR, police=TITRE)
        texte(s, 8.0, y + 0.5, 4.5, 0.4, detail, taille=15, couleur=DOUX)

    # 4. Du concept à la construction (croquis)
    s = d.slide("Du concept à la construction", notes=notes[4])
    texte(s, 0.8, 1.7, 4.6, 1.0, "« Une fenêtre vers son univers »", taille=24, couleur=OR_CLAIR,
          police=TITRE, italique=True)
    image(s, img[(4, "Image 4")], 0.9, 2.85, 4.4, 3.85, nom="Croquis de l'accueil", fond="F4EEE2")
    image(s, img[(4, "Image 6")], 5.9, 1.65, 6.6, 5.1, nom="Croquis de l'arborescence", fond="F4EEE2")

    # 5. Schéma fonctionnel
    s = d.slide("Le schéma fonctionnel", "Pourquoi Wagtail : son arbre de pages colle à cette structure",
                notes=notes[5])
    image(s, img[(5, "Image 4")], 0.9, 1.65, 11.5, 5.15, nom="Schéma fonctionnel")

    # 6. Wireframes
    s = d.slide("Les wireframes", "15 maquettes avant la première ligne de code", notes=notes[6])
    for k, nom in enumerate(["Image 9", "Image 5", "Image 7"]):
        image(s, img[(6, nom)], 0.9 + k * 3.25, 1.75, 2.7, 5.0)
    carte(s, 10.75, 2.4, 1.85, 3.7)
    texte(s, 10.9, 2.6, 1.55, 3.4, [[("Gris", {"gras": True, "couleur": "C9C9C9"})], [("la structure", {"couleur": DOUX})],
                                    [("", {})],
                                    [("Ocre", {"gras": True, "couleur": "B89A3A"})], [("ce que le client modifie", {"couleur": DOUX})]],
          taille=15, align=PP_ALIGN.CENTER)

    # 7. Environnement
    s = d.slide("Un environnement contrôlé", notes=notes[7])
    code(s, 0.8, 1.75, 6.3, 3.2, ["python -m venv env", "env\\Scripts\\activate", "pip install wagtail",
                                    "wagtail start Tales_Omnibus", "py manage.py migrate",
                                    "py manage.py createsuperuser", "py manage.py runserver"],
         taille=16, legende="Terminal")
    texte(s, 0.8, 5.4, 6.3, 0.9, [[("Un projet construit en local, ", {}), ("dans un environnement fermé", {"couleur": OR_CLAIR})]],
          taille=18, align=PP_ALIGN.CENTER)
    carte(s, 7.7, 1.75, 4.8, 4.9)
    texte(s, 8.0, 1.95, 4.2, 0.6, "Repository Git", taille=26, couleur=OR_CLAIR, police=TITRE, align=PP_ALIGN.CENTER)
    for k, ligne in enumerate(["Partagé gratuitement", "Réutilisable pour tout client", "Produit clé en main"]):
        pastille(s, 8.25, 3.0 + k * 1.1, 3.7, 0.7, ligne, taille=17)

    # 8. Configuration Wagtail
    s = d.slide("La configuration Wagtail", "Deux profils", notes=notes[8])
    image(s, img[(8, "Image 12")], 0.8, 1.7, 1.25, 5.1, nom="Menu de l'admin")
    texte(s, 2.45, 1.7, 3.8, 0.6, "Admin MJ", taille=26, couleur=OR_CLAIR, police=TITRE)
    texte(s, 2.45, 2.25, 3.8, 0.4, "Un accès complet", taille=16, couleur=DOUX, italique=True)
    apps = ["wagtail", "wagtail.admin", "wagtail.search", "wagtail.images", "wagtail.documents",
            "wagtail.snippets", "wagtail.users", "wagtail.sites", "wagtail.embeds",
            "wagtail.contrib.settings", "wagtail.contrib.sitemaps", "wagtail.contrib.redirects",
            "wagtail.contrib.forms"]
    code(s, 2.45, 2.8, 4.1, 4.0, apps, taille=12, legende="INSTALLED_APPS")
    texte(s, 7.2, 1.7, 5.3, 0.6, "Joueurs isolés", taille=26, couleur=OR_CLAIR, police=TITRE)
    texte(s, 7.2, 2.25, 5.3, 0.4, "Restreint à une seule page : la fiche de son héros", taille=16,
          couleur=DOUX, italique=True)
    image(s, img[(8, "Image 9")], 7.2, 3.0, 5.3, 2.9, nom="Droits d'un joueur")
    texte(s, 7.2, 6.15, 5.3, 0.5, "Groupe créé tout seul à la publication de la fiche", taille=15,
          align=PP_ALIGN.CENTER)

    # 9. Démonstration (intercalaire)
    d.couverture(None, "Démonstration client", "Vous voulez commencer votre Omnibus ?", notes[9])

    # 10. Interface graphique
    s = d.slide("L’interface graphique", "Du wireframe au thème", notes=notes[10])
    cadres = [("Image 4", "Wireframe"), ("Image 8", "Le site"), ("Image 10", "Thème Grimoire")]
    for k, (nom, legende) in enumerate(cadres):
        x = 0.8 + k * 4.05
        image(s, img[(10, nom)], x, 1.75, 3.55, 3.45)
        texte(s, x, 5.3, 3.55, 0.4, legende, taille=16, couleur=OR_CLAIR, align=PP_ALIGN.CENTER, police=TITRE)
        if k < 2:
            fleche(s, x + 3.6, 3.3, 0.38, 0.3)
    image(s, img[(10, "Image 12")], 5.2, 5.85, 1.75, 1.0, nom="Choix du thème")
    texte(s, 7.25, 5.95, 4.5, 0.8, [[("Adaptabilité", {"police": TITRE, "couleur": OR_CLAIR, "taille": 22})],
                                    [("6 thèmes, une seule mise en page", {"couleur": DOUX, "taille": 15})]])

    # 11. Encyclopédie
    s = d.slide("Encyclopédie et ses filtres", "Trois arborescences", notes=notes[11])
    numero(s, 0.8, 1.72, "I", d=0.5, taille=15)
    texte(s, 1.45, 1.75, 6, 0.45, "L’arbre des pages", taille=20, couleur=OR_CLAIR, police=TITRE)
    image(s, img[(11, "Image 8")], 0.85, 2.4, 8.4, 0.6, nom="Fil d'Ariane")
    numero(s, 0.8, 3.35, "III", d=0.5, taille=12)
    texte(s, 1.45, 3.38, 6, 0.45, "La géographie des cartes", taille=20, couleur=OR_CLAIR, police=TITRE)
    image(s, img[(11, "Image 10")], 0.85, 4.0, 8.4, 2.75, align="gauche", nom="Lieu sur les cartes")
    numero(s, 9.85, 1.72, "II", d=0.5, taille=14)
    texte(s, 10.5, 1.75, 2.2, 0.45, "Les catégories", taille=20, couleur=OR_CLAIR, police=TITRE)
    image(s, img[(11, "Image 6")], 9.85, 2.4, 2.65, 4.35, nom="Catégories")

    # 12. Connexions universelles
    s = d.slide("Pour des connexions universelles", notes=notes[12])
    image(s, img[(12, "Image 9")], 0.8, 1.7, 5.65, 4.55, nom="Filtres de l'encyclopédie")
    image(s, img[(12, "Image 6")], 6.85, 1.7, 5.65, 4.55, nom="Lieu d'origine et fiches liées")
    texte(s, 0.8, 6.35, 5.65, 0.4, "Filtrer : campagne, catégorie, lieu, tags", taille=16,
          couleur=OR_CLAIR, align=PP_ALIGN.CENTER, police=TITRE)
    texte(s, 6.85, 6.35, 5.65, 0.4, "Relier : le lieu d’origine, les fiches liées", taille=16,
          couleur=OR_CLAIR, align=PP_ALIGN.CENTER, police=TITRE)

    # 13. En ligne
    s = d.slide("En ligne", "quentin.bdx-certif-cms.tech", notes=notes[13])
    image(s, img[(13, "Image 4")], 0.8, 1.75, 9.0, 4.95, nom="Site en ligne")
    pile = ["VPS Hostinger", "Ubuntu", "nginx", "HTTPS"]
    rect(s, 11.33, 2.2, 0.03, 3.4, fond=BORD)
    for k, nom in enumerate(pile):
        pastille(s, 10.3, 1.9 + k * 1.15, 2.1, 0.6, nom, taille=17, gras=True)

    # 14 bis. Publier en une commande (C8)
    s = d.slide("Publier en une commande", "sudo publier",
                notes="≈ 45 s — C8, mise en ligne\n- J'ai écrit un script, « publier », qui fait toute la mise en "
                      "ligne en 6 étapes, et EXPLIQUE chacune (c'est fait pour un MJ qui ne connaît pas un serveur).\n"
                      "- 1 vérifie le projet ; 2 réglages de production (clé secrète, domaine, e-mail) gardés sur le "
                      "serveur, jamais dans Git ; 3 migrate + collectstatic ; 4 Gunicorn fait tourner Django en "
                      "service ; 5 Nginx reçoit les visiteurs et sert les fichiers statiques ; 6 HTTPS Let's Encrypt.\n"
                      "- Il se relance sans risque : ce qui existe déjà n'est pas écrasé (« local.py existe déjà : "
                      "on n'y touche pas »).\n- C'est la première brique de l'installeur clé en main.")
    etapes = [("1", "Vérifier le projet"), ("2", "Réglages de production"), ("3", "Base et fichiers statiques"),
              ("4", "Gunicorn"), ("5", "Nginx"), ("6", "HTTPS")]
    for k, (n, nom) in enumerate(etapes):
        y = 1.8 + k * 0.8
        numero(s, 0.8, y, n, d=0.55, taille=15)
        texte(s, 1.55, y + 0.02, 3.6, 0.5, nom, taille=19, couleur=OR_CLAIR, police=TITRE)
    texte(s, 0.8, 6.65 - 0.05, 4.4, 0.4, "Relancé sans risque : rien n’est écrasé", taille=14,
          couleur=DOUX, italique=True)
    if CAPTURE_PUBLIER.exists():
        image(s, CAPTURE_PUBLIER, 5.4, 1.75, 7.1, 4.95, nom="sudo publier")
    else:
        emplacement(s, 5.4, 1.75, 7.1, 4.95, "Le terminal de « sudo publier »",
                    "À enregistrer : rapport/slides/captures/sudo_publier.png")

    # 14. Tester, mesurer, entretenir
    s = d.slide("Tester, mesurer, entretenir", notes=notes[14])
    colonnes = [(0.8, "Tester"), (5.0, "Mesurer"), (9.0, "Entretenir")]
    for x, nom in colonnes:
        texte(s, x, 1.65, 3.7, 0.5, nom, taille=24, couleur=OR_CLAIR, police=TITRE)
    texte(s, 0.8, 2.15, 3.7, 0.4, "2 relecteurs · sur mobile", taille=15, couleur=DOUX, italique=True)
    texte(s, 0.8, 2.6, 0.8, 0.3, "Avant", taille=12, couleur=DOUX)
    image(s, img[(14, "Image 8")], 0.85, 2.95, 3.4, 1.4, align="gauche", nom="Relecteur avant")
    texte(s, 0.8, 4.5, 0.8, 0.3, "Après", taille=12, couleur=VERT)
    image(s, img[(14, "Image 6")], 0.85, 4.85, 3.4, 1.4, align="gauche", nom="Relecteur après")
    texte(s, 0.8, 6.45, 3.9, 0.45, [[("203 tests automatiques", {"gras": True})],
                                    [("préparés par IA · fonctionnalités", {"couleur": DOUX, "taille": 12})]],
          taille=14)
    texte(s, 5.0, 2.15, 3.7, 0.4, "Suivi statistique, sans cookie", taille=15, couleur=DOUX, italique=True)
    image(s, img[(14, "Image 11")], 5.05, 2.95, 3.6, 1.6, nom="GoatCounter")
    texte(s, 5.0, 4.9, 3.7, 1.0, "Sans cookie, donc sans bandeau.\nLe MJ connecté n’est pas compté.", taille=14,
          couleur=DOUX, align=PP_ALIGN.CENTER)
    texte(s, 9.0, 2.15, 3.7, 0.4, "Entretien en une commande", taille=15, couleur=DOUX, italique=True)
    pastille(s, 9.2, 3.1, 3.2, 0.7, "git pull", taille=17, police=CODE)
    rect(s, 10.65, 3.95, 0.3, 0.35, fond=OR, forme=MSO_SHAPE.DOWN_ARROW)
    pastille(s, 8.95, 4.45, 3.7, 0.7, "python manage.py entretien", taille=14, police=CODE)
    texte(s, 9.0, 5.4, 3.6, 1.2, "Sauvegarde · migrations · réparations · index", taille=14, couleur=DOUX,
          align=PP_ALIGN.CENTER)

    # 15. Bilan
    s = d.slide("Bilan", notes=notes[15])
    texte(s, 0.8, 1.65, 5.5, 0.5, "Les objectifs du cadrage", taille=20, couleur=DOUX, italique=True)
    for k, nom in enumerate(["Centralisation", "Exploration", "Autonomie", "Réseau"]):
        y = 2.3 + k * 1.1
        texte(s, 0.8, y, 3.3, 0.6, nom, taille=24, couleur=TEXTE, police=TITRE, ancre=MSO_ANCHOR.MIDDLE)
        rect(s, 4.0, y + 0.3, 1.2, 0.02, fond=BORD)
        pastille(s, 5.3, y + 0.05, 1.5, 0.5, "✓ validé", taille=15, fond="2E3A22", couleur="CFE3B8", gras=True)
    rect(s, 7.45, 1.7, 0.025, 5.0, fond=BORD)
    texte(s, 8.0, 1.65, 4.6, 0.5, "Avant la publication", taille=20, couleur=DOUX, italique=True)
    for k, nom in enumerate(["Installer clé en main", "Plusieurs univers", "Thèmes importables", "Packs d’icônes SVG"]):
        y = 2.3 + k * 1.1
        numero(s, 8.0, y + 0.02, str(k + 1), d=0.55, taille=16)
        texte(s, 8.8, y, 3.9, 0.6, nom, taille=22, couleur=TEXTE, police=TITRE, ancre=MSO_ANCHOR.MIDDLE)

    d.enregistrer()


# --- Partie 2 : le cas pratique SEO / accessibilité ------------------------
def partie_2():
    d = Deck(SORTIE_2, "Tales Omnibus · Cas pratique C7 · SEO et accessibilité")

    d.couverture("Soutenance · Cas pratique (C7)", "Optimiser le référencement\net l’accessibilité",
                 "Quentin Michelet · quentin.bdx-certif-cms.tech",
                 "Pas de temps compté. Annoncer le plan : la démarche, l'accessibilité (ce qui est fait, ce qui reste), "
                 "le SEO (ce qui est fait, ce qui reste), puis le bilan chiffré avant / après.")

    # 1. Démarche
    s = d.slide("Rappel du projet et démarche", "Pensé dès le début, pas ajouté à la fin",
                notes="≈ 1 min 30\n- POURQUOI C'EST IMPORTANT ICI : le site d'un MJ grandit et change sans arrêt, jusqu'à "
                      "200 à 300 pages. Impossible de soigner chaque page à la main : il fallait quelque chose de "
                      "FLEXIBLE, qui marche à tous les coups, quelle que soit la page ajoutée. C'est pour ça que je "
                      "m'y suis penché très tôt : le SEO et l'accessibilité sont dans les gabarits et le code "
                      "(titres, descriptions, ALT, h1, contrastes), pas à remplir page par page.\n"
                      "- Le site : l'univers d'un MJ, des centaines de fiches, un client qui ne code pas.\n"
                      "- Démarche : Lighthouse (ordinateur ET mobile, navigation privée) sur 4 pages types "
                      "(accueil, campagne, fiche, encyclopédie : les 3 pages mises en avant dans la présentation, "
                      "plus une fiche) + un test automatique qui parcourt TOUTES les pages de la démo.\n"
                      "- Résultat AVANT : SEO à 100 partout. Accessibilité à 100 sur ordinateur, mais 96 sur mobile "
                      "(4 pages) et 92 sur la fiche de lore : c'est là que j'ai creusé.\n"
                      "- Puis corrections dans l'ordre de l'impact, et chaque règle importante protégée par un test.")
    etapes = [("I", "Diagnostiquer", "Lighthouse sur 4 pages types\n+ audit de toutes les pages"),
              ("II", "Corriger", "Dans l’ordre de l’impact"),
              ("III", "Vérifier", "Un test par règle :\nelle ne recasse pas")]
    pastille(s, 0.8, 1.8, 4.7, 0.85, "200 à 300 pages qui changent :\nça doit marcher à tous les coups",
             taille=15, couleur=OR_CLAIR)
    for k, (n, nom, detail) in enumerate(etapes):
        y = 3.0 + k * 1.3
        numero(s, 0.8, y, n, d=0.7, taille=16 if len(n) < 3 else 13)
        texte(s, 1.75, y - 0.08, 3.7, 0.5, nom, taille=22, couleur=OR_CLAIR, police=TITRE)
        texte(s, 1.75, y + 0.4, 3.7, 0.8, detail, taille=14, couleur=DOUX)
    texte(s, 5.8, 1.35, 6.7, 0.35, "AVANT", taille=13, couleur=DOUX, gras=True, align=PP_ALIGN.RIGHT)
    grille_captures(s, "avant", 5.8, 1.75, 6.7, 4.95)

    # 2a. Accessibilité : structure et navigation
    s = d.slide("Accessibilité : structure et navigation",
                notes="≈ 2 min\n- UN seul h1 par page : sur l'accueil, c'est le nom du site ; ailleurs, le titre de la fiche. "
                      "Le test de la démo le vérifie sur toutes les pages.\n- Repères : article / aside / nav, header, main, footer.\n"
                      "- Recherche : libellé caché à l'écran (.sr-only) mais lu par les lecteurs d'écran.\n"
                      "- Focus clavier visible ; prefers-reduced-motion coupe la neige et les reflets des thèmes.")
    puces(s, 0.8, 1.75, 5.4, 4.0, ["Un seul <h1> par page", "Repères : <article>, <aside>, <nav>",
                                   "Libellé caché .sr-only sur la recherche", "Focus clavier visible",
                                   "prefers-reduced-motion : animations coupées"], taille=18, espace=12)
    code(s, 0.8, 4.75, 5.4, 1.95, ["{% if page.pk == current_site.root_page.pk %}",
                                   '  <h1 class="site-name">{{ … site_name }}</h1>',
                                   "{% else %}",
                                   '  <span class="site-name">{{ … site_name }}</span>'],
         taille=12, legende="templates/base.html")
    texte(s, 6.6, 1.35, 5.9, 0.35, "APRÈS : 100 partout", taille=13, couleur=VERT, gras=True, align=PP_ALIGN.RIGHT)
    grille_captures(s, "apres", 6.6, 1.75, 5.9, 4.95, largeur_libelle=1.45)

    # 2b. Accessibilité : contenus et formulaires
    s = d.slide("Accessibilité : contenus et formulaires",
                notes="≈ 2 min\n- ALT AUTOMATIQUE : « Dossiers : Titre. Description ». Les dossiers sont les collections Wagtail, "
                      "le titre vient du nom du fichier. Un MJ qui ne remplit rien a quand même un ALT utile.\n"
                      "- Vignettes à côté d'un titre visible : alt=\"\" (décoratives, sinon le lecteur d'écran lit deux fois).\n"
                      "- Contrastes : l'ocre du wireframe assombri de 3 % (4,34 → 4,59:1) ; un test vérifie ≥ 4,5 pour CHAQUE thème.\n"
                      "- Formulaires : un libellé par champ, mention RGPD au moment de la collecte.")
    code(s, 0.8, 1.75, 6.2, 2.2, ["texte = nettoyer_titre(image.title)",
                                   "dossiers = dossiers_de(image)",
                                   "if dossiers:",
                                   "    texte = f\"{', '.join(dossiers)} : {texte}\"",
                                   "# + la description, si le MJ l'a écrite"],
         taille=13, legende="core/images.py · filtre {{ image|alt_auto }}")
    texte(s, 0.8, 4.25, 6.2, 0.5, [[("➜  ", {"couleur": OR}), ("« Lieu, Carte : Carte d’Ardenn. Carte du continent… »", {"italique": True})]],
          taille=17)
    puces(s, 0.8, 5.0, 6.2, 1.5, ["Vignettes décoratives : alt=\"\"", "Un libellé pour chaque champ de formulaire"],
          taille=16, espace=6)
    carte(s, 7.6, 1.75, 4.9, 4.95)
    texte(s, 7.9, 1.95, 4.3, 0.5, "Contrastes WCAG", taille=24, couleur=OR_CLAIR, police=TITRE, align=PP_ALIGN.CENTER)
    rect(s, 8.25, 2.75, 1.5, 1.0, fond="8C782C")
    texte(s, 8.25, 2.75, 1.5, 1.0, "Aa", taille=30, couleur="FFFFFF", align=PP_ALIGN.CENTER, ancre=MSO_ANCHOR.MIDDLE, police=TITRE)
    texte(s, 8.25, 3.85, 1.5, 0.4, "4,34 : 1", taille=16, couleur="E08A7A", align=PP_ALIGN.CENTER, gras=True)
    fleche(s, 9.95, 3.1, 0.4, 0.3)
    rect(s, 10.55, 2.75, 1.5, 1.0, fond="88742B")
    texte(s, 10.55, 2.75, 1.5, 1.0, "Aa", taille=30, couleur="FFFFFF", align=PP_ALIGN.CENTER, ancre=MSO_ANCHOR.MIDDLE, police=TITRE)
    texte(s, 10.55, 3.85, 1.5, 0.4, "4,59 : 1", taille=16, couleur="A9CF8C", align=PP_ALIGN.CENTER, gras=True)
    texte(s, 7.9, 4.55, 4.3, 1.9, "L’ocre du wireframe, assombri de 3 %.\nUn test vérifie ≥ 4,5 : 1\npour chacun des 6 thèmes.",
          taille=16, align=PP_ALIGN.CENTER, interligne=1.15)

    # 3. Accessibilité : améliorations
    s = d.slide("Accessibilité : ce qu’il reste", "Des améliorations honnêtes",
                notes="≈ 2 min\n- Lighthouse mobile a trouvé DEUX vrais défauts (fiche de lore : 92).\n"
                      "- 1) Les liens du pied de page (« Mentions légales », « Contact ») : zones à toucher trop petites "
                      "et trop serrées pour un doigt (WCAG 2.5.8 : au moins 24 × 24 px). Correction en CSS : un padding "
                      "agrandit la zone sans grossir le texte, 32 px de haut. Le pied de page est commun : toutes les "
                      "pages corrigées d'un coup.\n"
                      "- 2) L'étiquette « Événement » : texte blanc sur le vert choisi par le MJ, 4,18:1 (il faut 4,5). "
                      "Correction : le SITE choisit l'encre, blanc ou noir, celle qui contraste le mieux. "
                      "Mathématiquement, l'une des deux donne TOUJOURS au moins 4,58:1 : le MJ peut choisir n'importe "
                      "quelle couleur, son étiquette reste lisible. Un test le vérifie sur près de 5 000 couleurs.\n"
                      "- Ce qui reste : pas de test avec un VRAI lecteur d'écran sur les décors des thèmes ; "
                      "les zones de la carte interactive sont difficiles à parcourir au clavier.")
    texte(s, 0.8, 1.75, 5.6, 0.5, "Trouvé par Lighthouse, corrigé", taille=22, couleur=OR_CLAIR, police=TITRE)
    puces(s, 0.8, 2.35, 5.6, 2.1, ["Liens du pied de page trop petits : zone à toucher de 32 px",
                                   "Étiquette à 4,18 : 1 : encre blanche ou noire, choisie par le site"],
          taille=16, espace=10)
    texte(s, 0.8, 4.55, 5.6, 0.5, "Pistes pour la suite", taille=22, couleur=OR_CLAIR, police=TITRE)
    puces(s, 0.8, 5.15, 5.6, 1.5, ["Tester avec un vrai lecteur d’écran", "Carte interactive : zones au clavier"],
          taille=16, espace=8)
    texte(s, 6.75, 1.45, 2.7, 0.3, "Avant", taille=14, couleur=OR_CLAIR, gras=True, align=PP_ALIGN.CENTER)
    image(s, capture("avant_lore_mobile"), 6.75, 1.8, 2.7, 4.9)
    texte(s, 9.8, 1.45, 2.7, 0.3, "Après", taille=14, couleur=VERT, gras=True, align=PP_ALIGN.CENTER)
    image(s, capture("apres_lore_mobile"), 9.8, 1.8, 2.7, 1.25)
    fleche(s, 9.4, 2.27, 0.32, 0.26)
    texte(s, 9.8, 3.3, 2.7, 1.6, "Même fiche, même téléphone :\n92 → 100", taille=15, couleur=TEXTE,
          align=PP_ALIGN.CENTER, interligne=1.15)

    # 4a. SEO technique et performance
    s = d.slide("SEO : technique et performance",
                notes="≈ 1 min 30\n- Sitemap : wagtail.contrib.sitemaps, calculé à chaque visite, donc toujours à jour.\n"
                      "- robots.txt : ferme l'admin et la recherche (pages de résultats en noindex).\n"
                      "- Performance : vignettes en WebP (l'original n'est pas touché), loading=\"lazy\" hors du "
                      "premier écran, polices hébergées sur le site (plus d'appel à Google).")
    puces(s, 0.8, 1.75, 5.6, 2.6, ["Sitemap toujours à jour", "robots.txt : admin et recherche fermés",
                                   "Vignettes en WebP", "loading=\"lazy\" hors du premier écran"],
          taille=18, espace=10)
    code(s, 0.8, 4.4, 5.6, 2.3, ["User-agent: *", "Disallow: /admin/", "Disallow: /django-admin/",
                                 "Disallow: /search/", "Sitemap: https://quentin.bdx-certif-cms.tech/sitemap.xml"],
         taille=12, legende="/robots.txt")
    image(s, SLIDES / "captures" / "sitemap.jpg", 6.8, 1.75, 5.7, 4.95, nom="sitemap.xml en ligne")

    # 4b. Adresses automatiques (slugs)
    s = d.slide("SEO : des adresses automatiques", "Le MJ n’y touche pas, il ne peut pas les casser",
                notes="≈ 1 min 30\n- Le slug (la fin de l'adresse) est recalculé depuis le TITRE à chaque enregistrement : "
                      "sans accent, ligatures gardées (« Cœur-de-Corneille » → /coeur-de-corneille/), -2 si une page sœur "
                      "porte déjà ce nom.\n- Le champ est en LECTURE SEULE dans l'onglet Promotion : un MJ qui ne code pas "
                      "ne peut pas fabriquer une adresse illisible ou cassée.\n- Pages uniques (campagnes, encyclopédie, "
                      "univers, contact) : adresse fixe.\n- Le titre change ? Wagtail crée une redirection 301 depuis "
                      "l'ancienne adresse : les liens partagés sur Discord marchent toujours.")
    puces(s, 0.8, 1.75, 5.6, 2.7, ["Adresse = le titre, recalculée à chaque fois",
                                   "Champ en lecture seule pour le MJ",
                                   "Ligatures gardées : /coeur-de-corneille/",
                                   "Titre changé : redirection 301 automatique"],
          taille=17, espace=9)
    code(s, 0.8, 4.4, 5.6, 2.3, ['FieldPanel("slug", read_only=True,',
                                 '           heading="Adresse de la page")',
                                 "",
                                 "def slug_voulu(self):",
                                 "    return self.slug_fixe or slug_lisible(self.title)"],
         taille=12, legende="core/slugs.py · SlugAutomatiqueMixin")
    image(s, SLIDES / "captures" / "onglet_promotion.jpg", 6.8, 1.75, 5.7, 4.95, nom="Onglet Promotion")

    # 4c. Titres et descriptions automatiques
    s = d.slide("SEO : titres et descriptions automatiques", "200 à 300 fiches : impossible de tout remplir à la main",
                notes="≈ 2 min\n- POURQUOI c'est automatique : un MJ a 200 à 300 fiches. Personne ne remplit 300 titres et 300 "
                      "descriptions à la main : sans automatisme, la plupart des pages n'auraient rien.\n- Le MJ PEUT écrire son titre et sa description (onglet Promotion) : ils passent en premier.\n"
                      "- Sinon, TITRE = « Titre · Catégorie | Nom de l'univers » : la catégorie de la fiche "
                      "(ex. « Vaël, déesse des Brumes · Déité majeure | Tales Omnibus »). L'accueil : le nom du site seul.\n"
                      "- DESCRIPTION = l'accroche de la page (intro, sinon description de la carte, sinon synopsis), "
                      "sans HTML, coupée proprement à 155 caractères (au-delà, Google tronque).\n"
                      "- Rien du tout ? Une phrase avec la catégorie : « Titre : déité majeure de l'univers X. »\n"
                      "- Les articles sont faits de BLOCS codés en dur : un bloc « section » s'affiche toujours en <section> avec "
                      "son titre en <h2>. Le MJ range son texte en sections sans connaître le HTML, et la hiérarchie "
                      "des titres reste propre sur les 300 pages (sous le <h1> unique).\n"
                      "- Plus canonical et Open Graph : un bel aperçu quand on colle le lien sur Discord.")
    code(s, 0.8, 1.75, 6.1, 2.75, ["if page.search_description:      # écrite par le MJ",
                                   "    return page.search_description",
                                   "for champ in CHAMPS_DESCRIPTION:  # intro, synopsis…",
                                   "    texte = texte_brut(getattr(page, champ, \"\"))",
                                   "    if texte:",
                                   "        return couper(texte)       # 155 caractères"],
         taille=12, legende="core/seo.py · description_seo()")
    texte(s, 0.8, 4.75, 6.1, 0.4, "Le titre de l’onglet, sans rien remplir :", taille=14, couleur=DOUX, italique=True)
    pastille(s, 0.8, 5.2, 6.1, 0.6, "Vaël, déesse des Brumes · Déité majeure | Tales Omnibus", taille=14)
    puces(s, 0.8, 6.0, 6.1, 0.8, ["Articles en blocs : chaque section = <section> + <h2>"], taille=15, espace=4)
    image(s, capture("apres_lore_ordi"), 7.3, 1.75, 5.2, 2.4)
    texte(s, 7.3, 4.45, 5.2, 1.2, [[("SEO : 100", {"couleur": VERT, "gras": True})],
                                   [("sur les 4 pages, ordinateur et mobile,", {})],
                                   [("avant comme après", {})]],
          taille=17, align=PP_ALIGN.CENTER, interligne=1.1)

    # 5. SEO améliorations
    s = d.slide("SEO : ce qu’il reste", "Des améliorations honnêtes",
                notes="≈ 1 min\n- Lighthouse est à 100 partout : il ne signale plus rien. Mais un score de 100 vérifie la "
                      "technique d'une page, pas le référencement réel (être trouvé, avoir des liens, du contenu qui "
                      "répond aux recherches).\n- Données structurées schema.org (fiches, événements).\n"
                      "- Images d'origine encore lourdes (les vignettes, elles, sont en WebP).\n"
                      "- Sous-domaine de la formation : pas de vrai nom de domaine, pas encore de Search Console.\n"
                      "- La description de l'accueil est générique : à écrire dans l'onglet Promotion.")
    pistes = [("Données structurées", "schema.org pour les fiches et les événements"),
              ("Images d’origine", "encore lourdes, les vignettes sont en WebP"),
              ("Nom de domaine", "un vrai domaine, puis la Search Console"),
              ("Accueil", "écrire sa description (onglet Promotion)")]
    for k, (nom, detail) in enumerate(pistes):
        y = 1.8 + k * 1.2
        numero(s, 0.8, y + 0.05, str(k + 1), d=0.6, taille=16)
        texte(s, 1.65, y, 4.8, 0.45, nom, taille=21, couleur=OR_CLAIR, police=TITRE)
        texte(s, 1.65, y + 0.47, 4.8, 0.4, detail, taille=15, couleur=DOUX)
    carte(s, 6.8, 1.75, 5.7, 4.95)
    texte(s, 7.1, 2.0, 5.1, 0.6, "100 ≠ terminé", taille=30, couleur=OR_CLAIR, police=TITRE, align=PP_ALIGN.CENTER)
    texte(s, 7.1, 2.9, 5.1, 3.5,
          "Lighthouse ne signale plus rien : il vérifie la technique d’une page.\n\n"
          "Il ne voit pas si le site est trouvé, ni si son contenu répond à ce que cherchent les joueurs "
          "et les spectateurs.\n\nC’est là que se jouent les prochaines étapes.",
          taille=16, align=PP_ALIGN.CENTER, interligne=1.15)

    # 6. Synthèse
    s = d.slide("Synthèse", notes="≈ 1 min 30\n- Lire la phrase, puis commenter le tableau : où ça a le plus progressé, "
                                  "et ce qui ne dépend pas de moi (hébergement).\n- Finir sur : « Merci, je suis prêt pour vos questions. »")
    carte(s, 0.8, 1.7, 11.7, 1.55)
    texte(s, 1.2, 1.8, 10.9, 1.35,
          "« J’ai d’abord automatisé ce qu’un MJ qui ne code pas oublierait (titres, descriptions, ALT, sitemap), "
          "puis vérifié par des tests ce qui casserait sans qu’on le voie (h1 unique, ALT, contrastes). »",
          taille=18, couleur=TEXTE, police=TITRE, italique=True, align=PP_ALIGN.CENTER, ancre=MSO_ANCHOR.MIDDLE)
    lignes = [NOMS_DES_PAGES[page] for page in PAGES_AUDITEES]
    entetes = ["Lighthouse", "Accessibilité\nordinateur avant", "Accessibilité\nordinateur après",
               "Accessibilité\nmobile avant", "Accessibilité\nmobile après", "SEO"]
    tableau = s.shapes.add_table(len(lignes) + 1, len(entetes), Inches(0.8), Inches(3.6), Inches(11.7), Inches(3.1)).table
    tableau.columns[0].width = Inches(2.7)
    for c in range(1, len(entetes)):
        tableau.columns[c].width = Inches(1.8)
    for r in range(len(lignes) + 1):
        for c in range(len(entetes)):
            cell = tableau.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(SURFACE_2 if r == 0 else (SURFACE if r % 2 else "251D16"))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tcpr = cell._tc.get_or_add_tcPr()
            for cote in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                ln = etree.Element(qn(cote), w=str(Pt(0.75)))
                plein = etree.SubElement(ln, qn("a:solidFill"))
                etree.SubElement(plein, qn("a:srgbClr"), val=BORD)
                tcpr.append(ln)
            # Le remplissage doit venir APRÈS les bordures dans le XML
            remplissage = tcpr.find(qn("a:solidFill"))
            if remplissage is not None:
                tcpr.remove(remplissage)
                tcpr.append(remplissage)
            tf = cell.text_frame
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            if r == 0:
                valeur, couleur, police, taille = entetes[c], OR_CLAIR, TITRE, 13
            elif c == 0:
                valeur, couleur, police, taille = lignes[r - 1], TEXTE, CORPS, 17
            else:
                score = SCORES[PAGES_AUDITEES[r - 1]][c - 1]
                if score is None:
                    valeur, couleur = "…", DOUX
                else:
                    valeur, couleur = str(score), VERT if score == 100 else OR_CLAIR
                police, taille = CORPS, 20
            for i, morceau in enumerate(valeur.split("\n")):
                para = p if i == 0 else tf.add_paragraph()
                para.alignment = p.alignment
                run = para.add_run()
                run.text = morceau
                run.font.size, run.font.color.rgb, run.font.name = Pt(taille), rgb(couleur), police
                run.font.bold = r == 0
    # Le style de tableau par défaut (bandes bleues) est remplacé par nos couleurs
    tbl = tableau._tbl
    tblpr = tbl.tblPr
    tblpr.set("firstRow", "0")
    tblpr.set("bandRow", "0")
    coins(s, 0.8, 3.6, 11.7, 3.1)

    d.enregistrer()


if __name__ == "__main__":
    dossier = Path(__file__).resolve().parent / "_habillage"
    dossier.mkdir(exist_ok=True)
    FOND_IMG = dossier / "fond_cuir.jpg"
    LOGO_IMG = dossier / "logo_dore.png"
    BANNIERE_IMG = dossier / "banniere_doree.png"
    fond_cuir(FOND_IMG)
    svg_en_png(IMG_SITE / "logo-tales-omnibus.svg", LOGO_IMG, 200)
    BANNIERE_RATIO = svg_en_png(IMG_SITE / "banniere-tales-omnibus.svg", BANNIERE_IMG, 700)
    partie_1()
    partie_2()
