"""
Redessine le logo Tales Omnibus (monogramme T dans un O) en SVG exact.
Toute la géométrie vient de deux cercles concentriques, d'une barre, d'une
jambe et d'une fente en diagonale ; tous les espaces font ESPACE px.
"""
import math
import sys

CX, CY = 512, 521          # centre de l'anneau (ajusté par moindres carrés sur le contour)
R, r = 356.5, 209          # rayons extérieur / intérieur du O
# Largeur de toutes les fentes : 30 (logo normal), plus pour les petites
# tailles (icône d'onglet), où une fente fine se referme
ESPACE = float(sys.argv[2]) if len(sys.argv) > 2 else 30
BARRE = (229, 143, 795, 278)       # x1, y1, x2, y2 de la barre du T
JAMBE = (443, 581)                 # x gauche / droite de la jambe du T
# La fente : son axe part de (540, 143) et descend vers la gauche
FENTE_X0, FENTE_Y0, PENTE = 540, 143, -0.0745   # x = X0 + PENTE * (y - Y0)

def axe(y):
    return FENTE_X0 + PENTE * (y - FENTE_Y0)

DEMI = ESPACE / 2
Y_COUDE = 693.3                                 # la fente devient verticale à cette hauteur
X_VERTICAL_DROIT = axe(Y_COUDE) + DEMI          # 514 avec des fentes de 30
X_VERTICAL_GAUCHE = axe(Y_COUDE) - DEMI         # 484 : la coupe basse de la moitié gauche du O

def sur_cercle(rayon, x=None, y=None, bas=True, droite=True):
    """Point du cercle de centre (CX, CY) à une abscisse ou une ordonnée donnée."""
    if x is not None:
        dy = math.sqrt(rayon ** 2 - (x - CX) ** 2)
        return x, CY + dy if bas else CY - dy
    dx = math.sqrt(rayon ** 2 - (y - CY) ** 2)
    return CX + dx if droite else CX - dx, y

def f(p):
    return f"{p[0]:.1f} {p[1]:.1f}"

def arc(rayon, fin, grand=0, sens=1):
    return f"A {rayon} {rayon} 0 {grand} {sens} {f(fin)}"

# --- 1. Moitié GAUCHE du T : barre gauche + jambe gauche, arrêtée par un arc
#        de rayon r - ESPACE (concentrique à l'anneau)
r_jambe = r - ESPACE
# Bas du bord gauche de la fente sur l'arc de la jambe : on cherche y tel que
# le point (axe(y) - DEMI, y) soit sur le cercle r_jambe
lo, hi = 600.0, 760.0
for _ in range(60):
    mid = (lo + hi) / 2
    x = axe(mid) - DEMI
    if (x - CX) ** 2 + (mid - CY) ** 2 > r_jambe ** 2:
        hi = mid
    else:
        lo = mid
bas_fente_gauche = (axe(lo) - DEMI, lo)
bas_jambe_gauche = sur_cercle(r_jambe, x=JAMBE[0], bas=True)
t_gauche = " ".join([
    f"M {BARRE[0]} {BARRE[1]}",
    f"L {f((axe(BARRE[1]) - DEMI, BARRE[1]))}",
    f"L {f(bas_fente_gauche)}",
    arc(r_jambe, bas_jambe_gauche, 0, 1),       # le long du bas, vers la gauche
    f"L {JAMBE[0]} {BARRE[3]}",
    f"L {BARRE[0]} {BARRE[3]}",
    "Z",
])

# --- 2. Moitié DROITE du T : barre droite + jambe droite, posée sur le bord
#        extérieur du O ; la fente devient verticale à x = 514
bas_jambe_droite = sur_cercle(R, x=JAMBE[1], bas=True)
bas_fente_droite = sur_cercle(R, x=X_VERTICAL_DROIT, bas=True)
t_droite = " ".join([
    f"M {f((axe(BARRE[1]) + DEMI, BARRE[1]))}",
    f"L {BARRE[2]} {BARRE[1]}",
    f"L {BARRE[2]} {BARRE[3]}",
    f"L {JAMBE[1]} {BARRE[3]}",
    f"L {f(bas_jambe_droite)}",
    arc(R, bas_fente_droite, 0, 1),
    f"L {X_VERTICAL_DROIT} {Y_COUDE:.1f}",
    "Z",
])

# --- 3. Moitié GAUCHE du O
HAUT_O = BARRE[3] + ESPACE                       # 308 : coupé à plat sous la barre
coupe_haute_g = JAMBE[0] - ESPACE                 # 413
o_gauche = " ".join([
    f"M {coupe_haute_g} {HAUT_O}",
    f"L {f(sur_cercle(R, y=HAUT_O, droite=False))}",
    arc(R, sur_cercle(R, x=X_VERTICAL_GAUCHE, bas=True), 0, 0),   # tout le côté gauche
    f"L {f(sur_cercle(r, x=X_VERTICAL_GAUCHE, bas=True))}",
    arc(r, sur_cercle(r, x=coupe_haute_g, bas=False), 0, 1),
    "Z",
])

# --- 4. Moitié DROITE du O
coupe_droite = JAMBE[1] + ESPACE                  # 611
o_droite = " ".join([
    f"M {coupe_droite} {HAUT_O}",
    f"L {f(sur_cercle(R, y=HAUT_O, droite=True))}",
    arc(R, sur_cercle(R, x=coupe_droite, bas=True), 0, 1),
    f"L {f(sur_cercle(r, x=coupe_droite, bas=True))}",
    arc(r, sur_cercle(r, x=coupe_droite, bas=False), 0, 0),
    "Z",
])

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="150 137 724 749" width="724" height="749">
  <title>Tales Omnibus</title>
  <!-- Monogramme T dans un O, fendu d'un coup d'épée. Géométrie exacte :
       anneau de centre (512, 521), rayons 356,5 et 209 ; fentes de {ESPACE} px.
       Une seule couleur, fond transparent : prêt pour « Dorer le logo ». -->
  <g fill="#000">
    <path d="{t_gauche}"/>
    <path d="{t_droite}"/>
    <path d="{o_gauche}"/>
    <path d="{o_droite}"/>
  </g>
</svg>
"""
sortie = sys.argv[1]
with open(sortie, "w", encoding="utf-8") as fichier:
    fichier.write(svg)
print(f"coude de la fente : y = {Y_COUDE:.1f} ; bas de la fente gauche : {f(bas_fente_gauche)}")
print(svg)
