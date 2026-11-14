"""
Les polices des thèmes : chargées depuis Google Fonts, ou hébergées sur le site.

Pourquoi c'est une question de RGPD : quand le navigateur du visiteur
télécharge une police chez Google, il envoie son adresse IP à Google
(un tribunal allemand a condamné un site pour ça en 2022). Deux solutions :
  - le DIRE dans les mentions légales (fait automatiquement : voir
    theme_utilise_google_fonts, lu par MentionsLegalesPage) ;
  - ou HÉBERGER les polices sur le site : manage.py heberger_polices
    télécharge les fichiers une fois pour toutes, et le thème ne parle plus
    à Google. La mention disparaît alors toute seule.
"""
import re
from pathlib import Path

from django.contrib.staticfiles import finders

# La ligne qui charge les polices, en tête de chaque thème
IMPORT_GOOGLE = re.compile(r'@import url\("(https://fonts\.googleapis\.com/[^"]+)"\);')
# Dans la feuille de Google : un bloc @font-face par police ET par alphabet,
# précédé d'un commentaire qui nomme l'alphabet (/* latin */, /* cyrillic */…)
BLOC_FONT_FACE = re.compile(r"/\* ([a-z-]+) \*/\s*(@font-face \{.*?\})", re.S)
URL_DU_FICHIER = re.compile(r"url\((https://fonts\.gstatic\.com/[^)]+)\)")
# Le français n'a besoin que de ces deux alphabets (« latin-ext » : œ, Œ…)
ALPHABETS_GARDES = {"latin", "latin-ext"}


def chemin_du_theme(theme):
    """Le fichier CSS d'un thème (static/css/themes/<clé>.css), ou None."""
    return finders.find(f"css/themes/{theme}.css") if theme else None


def theme_utilise_google_fonts(theme):
    """True si le thème charge encore ses polices chez Google."""
    chemin = chemin_du_theme(theme)
    return bool(chemin) and bool(IMPORT_GOOGLE.search(Path(chemin).read_text(encoding="utf-8")))


def garder_les_alphabets_utiles(css_google):
    """Les blocs @font-face latin / latin-ext seulement (pas de cyrillique ni de vietnamien)."""
    return [bloc for alphabet, bloc in BLOC_FONT_FACE.findall(css_google) if alphabet in ALPHABETS_GARDES]


def nom_de_fichier(url, index):
    """« https://fonts.gstatic.com/s/cinzel/v23/abc.woff2 » -> « cinzel-3.woff2 »."""
    morceaux = url.split("/")
    famille = morceaux[4] if len(morceaux) > 4 else "police"
    return f"{famille}-{index}.woff2"
