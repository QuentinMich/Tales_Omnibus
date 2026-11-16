"""
Dessine la BANNIÈRE Tales Omnibus d'après le croquis de Quentin : le
monogramme « déconstruit ».

        ┌─────────┬─────────┐
              │  A L E S
              │ ╭─╮
              │ │ │ m n i b u s
              │ ╰─╯

  - un GRAND T qui tient toute la hauteur : sa barre couvre le haut, sa
    jambe descend jusqu'au bas de la 2e ligne ;
  - « ALES » sous la barre, à droite de la jambe ;
  - le O posé au pied de la jambe, suivi de « mnibus » en minuscules.

Le T et le O gardent la géométrie du logo (vectoriser_logo.py) : mêmes
épaisseurs (barre 135, jambe 138, anneau de rayons 356,5 et 209) et même
coup d'épée (fente de 30 en diagonale, qui devient verticale). Seules la
longueur de la jambe et celle de la barre changent.

Les mots sont écrits avec de vraies polices, déjà hébergées par le site,
converties en TRACÉS : un SVG utilisé comme pochoir (mask) ne charge aucune
police, et un texte dépendrait de celles du visiteur.
  - « ALES » : Cinzel 700 (capitales gravées du thème Grimoire) ;
  - « mnibus » : EB Garamond 600 (Cinzel n'a pas de minuscules).
Les deux sont sous licence SIL OFL : on peut les intégrer à un logo.

Usage (fontTools et brotli nécessaires, PAS dans requirements.txt : c'est un
outil de dessin, pas une dépendance du site) :
    python banniere_logo.py sortie.svg
"""
import math
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

POLICES = "../Tales_Omnibus/Tales_Omnibus/static/fonts/"

# --- Mesures du logo (vectoriser_logo.py) -----------------------------------
ESPACE = 30                       # largeur de toutes les fentes
DEMI = ESPACE / 2
R, r = 356.5, 209                 # rayons du O
# Le T de la bannière est PLUS GRAS que celui du logo (demande de Quentin) :
# il porte toute la hauteur, avec l'épaisseur du logo il paraissait maigre.
GRAS_T = 1.5
EP_BARRE = 135 * GRAS_T                              # barre du logo : 135
JAMBE = (512 - 69 * GRAS_T, 512 + 69 * GRAS_T)       # jambe du logo : 443 à 581
PENTE = -0.0745                   # le coup d'épée : x recule quand y descend
LONG_DIAGONALE = 550.3            # longueur (en y) de la partie diagonale

# --- Mise en page, en proportion de la HAUTEUR du T (mesurée sur le croquis)
HAUT = 0
H = 2 * R / 0.42                  # le O fait 42 % de la hauteur : ~1698
BAS = HAUT + H                    # bas de la jambe = ligne de base de la 2e ligne
CENTRE_JAMBE = (JAMBE[0] + JAMBE[1]) / 2
DEMI_BARRE = 0.52 * H             # la barre déborde autant à gauche qu'à droite
BARRE = (CENTRE_JAMBE - DEMI_BARRE, HAUT, CENTRE_JAMBE + DEMI_BARRE, HAUT + EP_BARRE)


def f(p):
    return f"{p[0]:.1f} {p[1]:.1f}"


# --- Le coup d'épée -----------------------------------------------------------
class Fente:
    """Une fente qui part de (x0, y0), descend en diagonale, puis à la verticale."""

    def __init__(self, x0, y0):
        self.x0, self.y0 = x0, y0
        self.y_coude = y0 + LONG_DIAGONALE

    def axe(self, y):
        return self.x0 + PENTE * (min(y, self.y_coude) - self.y0)

    def bord(self, y, cote):
        return self.axe(y) + cote * DEMI


# --- Le T : barre + jambe, fendu, la jambe coupée à plat en bas --------------
# Même départ de fente que le logo : 28 px à droite du centre de la jambe
fente_t = Fente(CENTRE_JAMBE + 28, HAUT)
coude_g = (fente_t.bord(fente_t.y_coude, -1), fente_t.y_coude)
coude_d = (fente_t.bord(fente_t.y_coude, 1), fente_t.y_coude)
t_gauche = " ".join([
    f"M {BARRE[0]:.1f} {HAUT}",
    f"L {f((fente_t.bord(HAUT, -1), HAUT))}",
    f"L {f(coude_g)}",
    f"L {coude_g[0]:.1f} {BAS:.1f}",
    f"L {JAMBE[0]} {BAS:.1f}",
    f"L {JAMBE[0]} {BARRE[3]}",
    f"L {BARRE[0]:.1f} {BARRE[3]}",
    "Z",
])
t_droite = " ".join([
    f"M {f((fente_t.bord(HAUT, 1), HAUT))}",
    f"L {BARRE[2]:.1f} {HAUT}",
    f"L {BARRE[2]:.1f} {BARRE[3]}",
    f"L {JAMBE[1]} {BARRE[3]}",
    f"L {JAMBE[1]} {BAS:.1f}",
    f"L {coude_d[0]:.1f} {BAS:.1f}",
    f"L {f(coude_d)}",
    "Z",
])

# --- Le O : au pied de la jambe, fendu par son propre coup d'épée ------------
ECART_O = 0.07 * H                          # entre la jambe et le O
CX, CY = JAMBE[1] + ECART_O + R, BAS - R    # le bas du O sur la ligne de base
# Même fente que dans le logo : elle part 28 px à droite du centre, 378 au-dessus
fente_o = Fente(CX + 28, CY - 378)


def croise(rayon, cote, haut):
    """Point où un bord de la fente du O coupe un cercle (en haut ou en bas)."""
    lo, hi = (CY - rayon, CY) if haut else (CY, CY + rayon)
    dedans = lambda y: (fente_o.bord(y, cote) - CX) ** 2 + (y - CY) ** 2 < rayon ** 2
    for _ in range(80):
        mid = (lo + hi) / 2
        if dedans(mid) == haut:
            hi = mid
        else:
            lo = mid
    y = (lo + hi) / 2
    return fente_o.bord(y, cote), y


def arc(rayon, debut, fin, sens):
    """Arc de debut à fin ; sens=1 : horaire à l'écran (y vers le bas)."""
    angle = lambda p: math.atan2(p[1] - CY, p[0] - CX)
    balayage = (angle(fin) - angle(debut)) * (1 if sens else -1) % (2 * math.pi)
    return f"A {rayon} {rayon} 0 {1 if balayage > math.pi else 0} {sens} {f(fin)}"


def moitie_du_o(cote):
    """cote=-1 : moitié gauche du O ; +1 : moitié droite."""
    haut_ext, bas_ext = croise(R, cote, True), croise(R, cote, False)
    haut_int, bas_int = croise(r, cote, True), croise(r, cote, False)
    sens = 0 if cote < 0 else 1          # la moitié gauche fait le tour par la gauche
    return " ".join([
        f"M {f(haut_ext)}",
        arc(R, haut_ext, bas_ext, sens),
        f"L {f(bas_int)}",               # remonte le long de la fente
        arc(r, bas_int, haut_int, 1 - sens),
        "Z",                             # retour au départ le long de la fente
    ])


# --- Les mots, en tracés -------------------------------------------------------
class Police:
    def __init__(self, fichier, graisse):
        police = instantiateVariableFont(TTFont(POLICES + fichier), {"wght": graisse})
        self.glyphes, self.avances = police.getGlyphSet(), police["hmtx"]
        self.carte = police.getBestCmap()
        self.os2 = police["OS/2"]

    def mot(self, texte, x, base, echelle, approche):
        """Le mot en tracés, de x à droite, sur la ligne de base. -> (d, x de fin)"""
        morceaux = []
        for lettre in texte:
            nom = self.carte[ord(lettre)]
            # Coordonnées au dixième : fichier deux fois plus léger, rien de visible
            stylo = SVGPathPen(self.glyphes, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
            # Police : y vers le HAUT ; SVG : y vers le BAS -> on retourne l'axe
            self.glyphes[nom].draw(TransformPen(stylo, (echelle, 0, 0, -echelle, x, base)))
            morceaux.append(stylo.getCommands())
            x += (self.avances[nom][0] + approche) * echelle
        return " ".join(morceaux), x - approche * echelle


cinzel = Police("grimoire/cinzel-2.woff2", 700)
garamond = Police("grimoire/ebgaramond-8.woff2", 600)

# « ALES » : capitales de 21 % de H, ligne de base à 49 % de H, à 13 % de H de la jambe
ech_ales = 0.21 * H / cinzel.os2.sCapHeight
ales, fin_ales = cinzel.mot("ALES", JAMBE[1] + 0.13 * H, HAUT + 0.49 * H, ech_ales, 60)

# « mnibus » : hauteur d'x de 14,5 % de H (plus petit que ALES : T > O > ALES > mnibus),
# sur la ligne de base, juste après le O
ech_mnibus = 0.145 * H / garamond.os2.sxHeight
mnibus, fin_mnibus = garamond.mot("mnibus", CX + R + 0.05 * H, BAS, ech_mnibus, 30)

x0 = BARRE[0]
x1 = max(fin_ales, fin_mnibus, BARRE[2])
largeur, hauteur = x1 - x0, BAS - HAUT

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {HAUT} {largeur:.1f} {hauteur:.1f}" width="{largeur:.0f}" height="{hauteur:.0f}">
  <title>Tales Omnibus</title>
  <!-- Bannière : le monogramme déconstruit (croquis de Quentin). T et O :
       géométrie du logo (anneau de rayons 356,5 et 209, fentes de {ESPACE}).
       ALES : Cinzel 700 ; mnibus : EB Garamond 600 (SIL OFL), en tracés.
       Une seule couleur, fond transparent : faite pour servir de pochoir. -->
  <g fill="#000">
    <path d="{t_gauche}"/>
    <path d="{t_droite}"/>
    <path d="{moitie_du_o(-1)}"/>
    <path d="{moitie_du_o(1)}"/>
    <path d="{ales}"/>
    <path d="{mnibus}"/>
  </g>
</svg>
"""
with open(sys.argv[1], "w", encoding="utf-8") as fichier:
    fichier.write(svg)
print(f"viewBox : {x0:.1f} {HAUT} {largeur:.1f} {hauteur:.1f} (rapport {largeur / hauteur:.3f})")
