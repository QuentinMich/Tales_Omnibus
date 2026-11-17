# Slides, partie 1 : présentation (10 min, viser 9)

D'après la consigne « Préparer ses slides, partie 1 » : 10 étapes dans cet
ordre, 12 à 15 slides maximum, une slide = une idée, montrer plutôt que
décrire, toujours dire le POURQUOI. Captures : `rapport/captures/`.

| # | Étape (compétence) | Slides | À montrer | À dire (le pourquoi) | Temps |
|---|---|---|---|---|---|
| 1 | Présentation perso | 1 | Ton nom, la formation Découverte Métier IA, Simplon Bordeaux | Joueur et MJ : le besoin vient de ta propre pratique. La suite : une formation en IA | 0:30 |
| 2 | Projet (C1) | 1 | Le client (MJ streamer), 4 objectifs du cadrage | « Que les spectateurs retrouvent l'histoire » : visibilité, encyclopédie, autonomie du MJ, contact | 1:00 |
| 3 | Cadre technique (C2) | 2 | a) `16_schema_fonctionnel` ; b) une planche de wireframes (`wf_planche_1`) | Pourquoi Wagtail : arbre de pages = campagnes > héros / cartes / chronologie ; StreamField ; Python. Les wireframes avant le code | 1:30 |
| 4 | Environnement (C3) | 1 | 4 étapes en frise : venv → Wagtail → apps (core, campagnes, encyclopédie…) → git | Un environnement isolé et versionné : refaire le site sur un autre PC en une commande | 0:45 |
| 5 | Paramétrage (C4) | 1 | `17_admin_droits_joueur` + menu admin réorganisé | Un joueur ne modifie QUE sa fiche : le groupe est créé tout seul à la publication. Menu renommé pour un client qui ne code pas | 1:00 |
| 6 | Démonstration | 1 | Slide de transition : « Place au site » + l'adresse | (on passe sur le site en direct) | — |
| 7 | Interfaces (C5) | 1 | `00_wireframe_campagne` à côté de `01_campagne_wireframe` + un thème (`09_grimoire_campagne`) | Fidèle au wireframe, puis 6 thèmes qui ne changent QUE les couleurs et décors : une seule mise en page à maintenir | 1:00 |
| 8 | Contenus (C6) | 1 | Encyclopédie et ses filtres (`06_encyclopedie_filtres`) | Catégories ≠ arbre des pages ; ALT automatique ; RGPD : mention sous les formulaires, polices hébergées, stats sans cookie | 1:00 |
| 9 | Déploiement (C8) | 2 | a) `18_site_en_ligne` (VPS Hostinger, Ubuntu, HTTPS) ; b) `19_goatcounter` + avant/après des relecteurs | Pourquoi un VPS (Python, pas du PHP mutualisé). Tests : 203 automatiques + relecteurs. Mise à jour : une commande (entretien) | 1:30 |
| 10 | Bilan (perspectives) | 1 | Objectifs atteints (cochés) + 2 ou 3 pistes (installeur clé en main, packs d'icônes) | Ce que tu en retiens, et la suite : l'éthique des IA | 0:45 |

**Total : 12 slides, environ 9 minutes.**

## Points d'attention
- L'étape 6 (Démo) est AU MILIEU du sommaire alors que la consigne annonce
  10 min de slides PUIS 10 min de démo : demander au formateur si les
  étapes 7 à 9 se présentent avant la démo, pendant, ou après. (La partie 2
  de la consigne est une AUTRE épreuve : le cas pratique SEO/accessibilité,
  voir plan_partie2.md.)
- Pas de pavé de texte : 1 capture + 3 mots-clés par slide, le reste à l'oral.
- Chronométrer à voix haute. Si ça dépasse 9 min, couper du texte, pas des captures.
