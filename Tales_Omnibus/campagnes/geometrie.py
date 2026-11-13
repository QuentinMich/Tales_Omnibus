"""
GÉOMÉTRIE DES CARTES : qui est dans qui ?

Sur une carte, un lieu est soit un POINT (une ville), soit une ZONE (un
royaume, une forêt), dessinée comme un polygone : une liste de sommets
[[x, y], [x, y], ...]. Toutes les coordonnées sont en % de l'image (0 à 100),
comme les étoiles.

Remarque : x est en % de la LARGEUR et y en % de la HAUTEUR. Sur une image
non carrée, ce n'est donc pas la même unité dans les deux sens. Aucune
importance ici : « être dedans » ne change pas quand on étire une image, et
étirer multiplie TOUTES les aires par le même nombre, donc le classement
« la plus petite zone » reste le même.

Que des fonctions « pures » (des nombres en entrée, des nombres en sortie) :
faciles à tester, sans base de données.
"""


def aire(polygone):
    """
    Aire d'un polygone, par la formule du lacet (« shoelace ») : on fait le
    tour des sommets en additionnant des produits en croix.
    """
    total = 0.0
    for (x1, y1), (x2, y2) in zip(polygone, polygone[1:] + polygone[:1]):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def centre(polygone):
    """
    Le centre de gravité de la zone (là où on la poserait en équilibre sur
    un doigt). Même famille de formule que l'aire. Si la forme est
    « plate » (aire nulle), on prend simplement la moyenne des sommets.

    Limite connue : pour une forme très creusée (un croissant), le centre
    peut tomber en dehors de la forme.
    """
    a = 0.0
    cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(polygone, polygone[1:] + polygone[:1]):
        croix = x1 * y2 - x2 * y1
        a += croix
        cx += (x1 + x2) * croix
        cy += (y1 + y2) * croix
    if abs(a) < 1e-9:
        n = len(polygone)
        return (sum(p[0] for p in polygone) / n, sum(p[1] for p in polygone) / n)
    a /= 2
    return (cx / (6 * a), cy / (6 * a))


def contient(polygone, x, y):
    """
    Le point (x, y) est-il dans le polygone ? Algorithme du RAYON : on tire
    une demi-droite horizontale depuis le point, vers la droite, et on
    compte combien de bords elle traverse. Nombre impair = dedans
    (on est entré sans ressortir), pair = dehors.
    """
    dedans = False
    for (x1, y1), (x2, y2) in zip(polygone, polygone[1:] + polygone[:1]):
        # Ce bord enjambe-t-il la hauteur du point ?
        if (y1 > y) != (y2 > y):
            # Abscisse où le bord croise la hauteur y
            x_croisement = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_croisement:
                dedans = not dedans
    return dedans


def ranger(elements):
    """
    Construit l'arbre d'une carte. Chaque élément est un dict :
        {'cle': ..., 'lieu': ..., 'point': (x, y) ou None, 'zone': [...] ou None}
    ('point' = l'étoile, ou le centre de la zone pour une zone).

    Renvoie {cle: cle_du_parent ou None}. Les règles :
      - un élément est rangé dans une ZONE qui contient son point ;
      - une zone ne peut contenir qu'une zone PLUS PETITE qu'elle
        (sinon deux zones pourraient se contenir l'une l'autre) ;
      - s'il y a plusieurs candidates, on prend la plus petite :
        la ville va dans le duché, le duché dans le royaume ;
      - un lieu ne peut pas être dans lui-même (même lieu dessiné deux fois).
    """
    zones = [(e, aire(e['zone'])) for e in elements if e.get('zone')]
    parents = {}
    for element in elements:
        parents[element['cle']] = None
        if element.get('point') is None:
            continue  # pas encore placé sur la carte
        x, y = element['point']
        taille = aire(element['zone']) if element.get('zone') else 0
        candidates = [
            (surface, zone['cle']) for zone, surface in zones
            if zone['cle'] != element['cle']
            and zone['lieu'] != element['lieu']
            and surface > taille
            and contient(zone['zone'], x, y)
        ]
        if candidates:
            parents[element['cle']] = min(candidates, key=lambda c: c[0])[1]
    return parents


def est_une_forme_valide(forme):
    """Au moins 3 sommets, chacun = deux nombres entre 0 et 100."""
    if not isinstance(forme, list) or len(forme) < 3:
        return False
    for sommet in forme:
        if not (isinstance(sommet, (list, tuple)) and len(sommet) == 2):
            return False
        for valeur in sommet:
            if isinstance(valeur, bool) or not isinstance(valeur, (int, float)) or not 0 <= valeur <= 100:
                return False
    return True
