# Slides, partie 2 : cas pratique SEO et accessibilité (15 min, viser 13 à 14)

D'après la consigne « Préparer ses slides, partie 2 » : une seule compétence
(C7, optimisation), environ 8 slides, une preuve par point (capture
Lighthouse, code de 3 à 5 lignes, ou les deux), améliorations HONNÊTES.

⚠️ À FAIRE AVANT : les scores Lighthouse (Chrome > F12 > Lighthouse, mode
navigation privée, ordinateur ET mobile), sur le site EN LIGNE, pages Accueil,
Campagne, une fiche, Encyclopédie. Pour l'« avant » : lancer une ancienne
version du site en local (commit d'avant le brief SEO) et la mesurer pareil.

| # | Étape | Slides | Preuve à montrer | À dire (le pourquoi) | Temps |
|---|---|---|---|---|---|
| 1 | Rappel du projet et démarche | 1 | Capture du site + le tableau Lighthouse AVANT | Diagnostic d'abord (Lighthouse + audit de toutes les pages par un test automatique), corrections ensuite, dans l'ordre de l'impact | 1:30 |
| 2a | Accessibilité : structure et navigation | 1 | Score Lighthouse a11y après + code : `{% if %}<h1>` unique / `:where(h1).site-name` | UN seul h1 par page (le nom du site sur l'accueil), `<article>`/`<aside>`/`<nav>`, libellé caché `.sr-only` sur la recherche, focus clavier visible, `prefers-reduced-motion` (neige, reflets coupés) | 2:00 |
| 2b | Accessibilité : contenus et formulaires | 1 | Code : `{% image page.main_image fill-600x850 alt=page.main_image\|alt_auto %}` + contraste | ALT automatique (dossiers + titre + description) ; vignettes décoratives en `alt=""` ; contrastes WCAG ≥ 4,5 vérifiés PAR UN TEST pour chaque thème (ocre assombri de 3 % : 4,34 → 4,59) ; labels des formulaires | 2:00 |
| 3 | Accessibilité : améliorations | 1 | Ce que Lighthouse signale encore | (à remplir avec le vrai rapport Lighthouse) Pistes honnêtes : décors des thèmes non testés avec un lecteur d'écran réel ; carte interactive difficile au clavier pour les zones | 1:30 |
| 4a | SEO : technique | 1 | `/sitemap.xml` qui répond + robots.txt (4 lignes) | Sitemap toujours à jour (calculé à chaque visite), robots.txt qui ferme l'admin et la recherche (`noindex`), adresses lisibles (`/campagnes/les-brumes-dardenn/`, ligatures gardées) + redirections 301 quand un titre change | 2:00 |
| 4b | SEO : contenus et performance | 1 | Score Lighthouse SEO + code source : `<title>` et `<meta description>` remplis | Titre et description AUTOMATIQUES si le client ne remplit rien (« Titre · Catégorie \| Univers », 155 caractères) ; canonical ; Open Graph (aperçu Discord) ; vignettes en WebP ; `loading="lazy"` hors du premier écran | 2:00 |
| 5 | SEO : améliorations | 1 | — | (à confirmer avec Lighthouse) Pistes : données structurées (schema.org), images d'origine encore lourdes, sous-domaine de la formation (pas de vrai nom de domaine), pas encore de Search Console | 1:00 |
| 6 | Synthèse et justification | 1 | 1 phrase + le tableau des scores avant/après | « J'ai d'abord automatisé ce qu'un MJ qui ne code pas oublierait (titres, descriptions, ALT, sitemap), puis vérifié par des tests ce qui casserait sans qu'on le voie (h1 unique, ALT, contrastes). » | 1:30 |

**Total : 8 slides, environ 13 min 30.**

## Extraits de code possibles (3 à 5 lignes)
- robots.txt (core/views.py) : `Disallow: /admin/`, `/django-admin/`, `/search/` + `Sitemap:`
- Le filtre ALT : `{{ image|alt_auto }}` → « Lieu, Ville : Port-Lanterne. … »
- `WAGTAILIMAGES_FORMAT_CONVERSIONS` (vignettes WebP, original intact)
- Le test qui vérifie « 1 h1 et aucune image sans alt » sur TOUTES les pages de la démo
