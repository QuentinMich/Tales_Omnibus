"""
L'admin Wagtail aux couleurs du thème du site.

Wagtail prévoit lui-même la personnalisation de ses couleurs : toute son
interface dérive de deux couleurs, données en TEINTE / SATURATION / LUMINOSITÉ
(--w-color-primary-hue, …) ; les nuances plus claires et plus foncées
(survol, fonds pâles) en sont CALCULÉES par Wagtail avec des calc().
On n'a donc que deux couleurs à fournir par thème :
  - primaire : le menu de gauche (fond sombre, texte blanc) ;
  - secondaire : les boutons et les liens (texte blanc dessus).
Les deux doivent rester lisibles avec du texte blanc : contraste ≥ 4,5
(vérifié par les tests, même formule WCAG que pour les thèmes du site).

Le CSS est injecté par le hook insert_global_admin_css (core/wagtail_hooks.py).
"""
import colorsys

# Thème -> (primaire = menu, secondaire = boutons). Tirées des thèmes du site.
COULEURS_ADMIN = {
    "": ("#3A3A3A", "#6E5E22"),            # wireframe : gris + ocre assombri (lisible)
    "grimoire": ("#3A2316", "#7A1C1C"),    # cuir de reliure + rouge sang
    "cyberpunk": ("#14102E", "#B0128F"),   # nuit + magenta profond
    "tenebres": ("#241D18", "#7E1414"),    # fer + sang
    "enquete": ("#141312", "#9B1C1C"),     # laque noire + encre des tampons
    "survivant": ("#22251F", "#8E1F1A"),   # béton + sang séché
}


def en_hsl(hexa):
    """« #7A1C1C » -> (0.0, 62.7, 29.4) : teinte en degrés, saturation et luminosité en %."""
    r, g, b = (int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5))
    teinte, luminosite, saturation = colorsys.rgb_to_hls(r, g, b)  # attention : H, L, S
    return round(teinte * 360, 1), round(saturation * 100, 1), round(luminosite * 100, 1)


def css_couleurs_admin(theme):
    """Les variables de Wagtail pour ce thème, dans un :root."""
    primaire, secondaire = COULEURS_ADMIN.get(theme or "", COULEURS_ADMIN[""])
    lignes = []
    for nom, hexa in (("primary", primaire), ("secondary", secondaire)):
        teinte, saturation, luminosite = en_hsl(hexa)
        lignes += [
            f"--w-color-{nom}-hue: {teinte};",
            f"--w-color-{nom}-saturation: {saturation}%;",
            f"--w-color-{nom}-lightness: {luminosite}%;",
        ]
    return ":root { " + " ".join(lignes) + " }"


def contraste_avec_le_blanc(hexa):
    """Rapport de contraste WCAG entre cette couleur et du texte blanc (1 à 21)."""
    def canal(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    luminance = 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)
    return 1.05 / (luminance + 0.05)
