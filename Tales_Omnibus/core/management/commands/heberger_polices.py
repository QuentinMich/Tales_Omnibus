"""
Héberge les polices des thèmes sur le site (RGPD : plus aucun appel à Google) :
    ../env/Scripts/python.exe manage.py heberger_polices
    ../env/Scripts/python.exe manage.py heberger_polices --theme grimoire

Pour chaque thème qui charge encore ses polices chez Google Fonts :
  1. télécharge la feuille de Google (en se présentant comme un navigateur
     récent, sinon Google ne propose pas le format woff2, le plus léger) ;
  2. garde les alphabets latin et latin-ext (le français n'a besoin de rien d'autre) ;
  3. télécharge chaque fichier de police dans static/fonts/<thème>/ ;
  4. écrit static/fonts/<thème>/polices.css, la même feuille avec des
     adresses LOCALES ;
  5. remplace la ligne @import du thème par un @import de cette feuille.

À lancer UNE fois, sur un seul ordi : les fichiers sont ensuite dans git,
comme le reste du CSS. Relancer ne fait rien pour un thème déjà hébergé.
"""
import urllib.request
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.models import THEMES
from core.polices import (
    IMPORT_GOOGLE, URL_DU_FICHIER, chemin_du_theme, garder_les_alphabets_utiles, nom_de_fichier,
)

# Un navigateur récent : c'est lui qui décide du format que Google renvoie
NAVIGATEUR = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def telecharger(url):
    requete = urllib.request.Request(url, headers={"User-Agent": NAVIGATEUR})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return reponse.read()


class Command(BaseCommand):
    help = "Télécharge les polices Google des thèmes dans static/fonts/ (plus d'appel à Google)."

    def add_arguments(self, parser):
        parser.add_argument("--theme", help="Un seul thème (clé : grimoire, cyberpunk…)")

    def handle(self, *args, theme=None, **options):
        cles = [cle for cle, _ in THEMES if cle]
        if theme and theme not in cles:
            raise CommandError(f"Thème inconnu : {theme}. Thèmes : {', '.join(cles)}")
        for cle in [theme] if theme else cles:
            self.heberger(cle)

    def heberger(self, cle):
        chemin_css = Path(chemin_du_theme(cle))
        texte = chemin_css.read_text(encoding="utf-8")
        trouve = IMPORT_GOOGLE.search(texte)
        if not trouve:
            self.stdout.write(f"{cle} : déjà hébergé, rien à faire.")
            return

        # static/css/themes/grimoire.css -> static/fonts/grimoire/
        dossier = chemin_css.parent.parent.parent / "fonts" / cle
        dossier.mkdir(parents=True, exist_ok=True)

        blocs = garder_les_alphabets_utiles(telecharger(trouve.group(1)).decode("utf-8"))
        if not blocs:
            raise CommandError(f"{cle} : Google n'a renvoyé aucune police latine.")
        feuille, poids, deja = [], 0, {}
        for bloc in blocs:
            url = URL_DU_FICHIER.search(bloc).group(1)
            # Une police « variable » sert plusieurs graisses avec UN fichier :
            # Google le cite dans plusieurs blocs, on ne le télécharge qu'une fois.
            if url not in deja:
                deja[url] = nom_de_fichier(url, len(deja) + 1)
                contenu = telecharger(url)
                (dossier / deja[url]).write_bytes(contenu)
                poids += len(contenu)
            feuille.append(bloc.replace(url, deja[url]))  # adresse relative : à côté de polices.css

        (dossier / "polices.css").write_text(
            f"/* Polices du thème {cle}, hébergées sur le site (manage.py heberger_polices). */\n\n"
            + "\n\n".join(feuille) + "\n",
            encoding="utf-8",
        )
        # Relatif au fichier du thème : css/themes/ -> ../../fonts/<thème>/
        nouvel_import = (f'/* Polices hébergées sur le site (RGPD) : manage.py heberger_polices */\n'
                         f'@import url("../../fonts/{cle}/polices.css");')
        chemin_css.write_text(texte.replace(trouve.group(0), nouvel_import), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(
            f"{cle} : {len(deja)} fichiers de police ({poids // 1024} Ko) dans static/fonts/{cle}/"
        ))
