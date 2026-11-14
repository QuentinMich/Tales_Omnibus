"""
Protection des SVG envoyés dans la médiathèque.

Un SVG n'est pas une image comme les autres : c'est du texte (XML) qui PEUT
contenir du JavaScript. Affiché avec <img src="logo.svg">, ce script ne
s'exécute jamais. Mais si quelqu'un ouvre directement l'adresse du fichier
(/media/…/logo.svg), le navigateur l'affiche comme une page du site, et le
script s'exécuterait avec les droits du site : il pourrait par exemple agir
avec la session d'un admin connecté.

Or les comptes joueurs peuvent envoyer des images. On ajoute donc, sur chaque
SVG servi depuis /media/, l'en-tête Content-Security-Policy qui interdit tout
script : le dessin s'affiche, le code ne tourne pas.

En PRODUCTION, les médias sont en général servis par le serveur web (nginx…)
et pas par Django : il faudra y ajouter le même en-tête (voir CLAUDE.md).
"""
from django.conf import settings

CSP_SVG = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox"


class SvgSansScriptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(settings.MEDIA_URL) and request.path.lower().endswith(".svg"):
            response["Content-Security-Policy"] = CSP_SVG
        return response
