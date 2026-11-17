"""
Contenu du rapport de certification de Tales Omnibus.
Balisage dans les textes : **gras**, `code`, _italique_.
"""
import os
RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..") + os.sep
_CAPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "captures")
CAPTURES = {os.path.splitext(f)[0]: os.path.join(_CAPT, f) for f in sorted(os.listdir(_CAPT))
            if os.path.isfile(os.path.join(_CAPT, f))}

COUVERTURE = {
    "titre": "TALES OMNIBUS",
    "date": "Novembre 2026",
    "auteur": "Quentin [NOM], apprenant · Découverte Métier IA, Simplon Bordeaux",
}

L = 9638  # largeur utile d'une page A4 avec les marges du template, en DXA

CONTENU = [
    # ================================================================ RÉSUMÉ
    ("h1", "Résumé exécutif"),
    ("p", "Un maître du jeu (MJ) de jeu de rôle, qui anime ses campagnes en direct sur Twitch et YouTube, veut "
          "faire connaître son univers, donner à ses spectateurs et à ses joueurs un endroit unique où "
          "retrouver l'histoire de ses campagnes, et proposer ses services de MJ. Ce besoin, d'abord le mien, "
          "est devenu celui d'un **client type** : le site est pensé pour être adopté par n'importe quel MJ, "
          "et distribué gratuitement."),
    ("p", "La solution, **Tales Omnibus**, est un site construit avec le CMS **Wagtail** (Python / Django). Il "
          "réunit des pages de campagnes (héros, cartes interactives, chronologie), une encyclopédie filtrable "
          "(lieux, personnages, créatures, légendes), une page Univers, un formulaire de contact et les "
          "mentions légales. Le MJ gère tout depuis l'administration, sans écrire une ligne de code : il "
          "place les lieux sur ses cartes à la souris, choisit parmi six thèmes graphiques et peut ouvrir à "
          "chaque joueur un accès limité à sa propre fiche."),
    ("p", "Le site est couvert par 201 tests automatisés, une campagne de démonstration complète s'installe "
          "en un clic, et il est en ligne à l'adresse https://quentin.bdx-certif-cms.tech, avec une mesure "
          "d'audience sans cookie."),

    # ================================================================ INTRODUCTION
    ("h1s", "Introduction"),
    ("h2", "Contexte du projet"),
    ("p", "Le premier commanditaire, c'est moi : maître du jeu, je voulais un site pour mon propre univers. "
          "En avançant, j'ai constaté que mon besoin était celui de beaucoup d'autres MJ. Le commanditaire est "
          "donc devenu un **client type** : un maître du jeu indépendant, souvent streamer, qui crée des "
          "campagnes longues dans un monde très détaillé (des royaumes, des villes, des personnages récurrents, "
          "des siècles d'histoire), les joue en direct sur Twitch, puis les publie en différé sur YouTube."),
    ("p", "Aujourd'hui, cet univers est dispersé : des notes personnelles, des messages épinglés sur Discord, "
          "des cartes partagées en image, des souvenirs dans les vidéos. Un spectateur qui arrive en cours "
          "de campagne n'a aucun moyen de rattraper l'histoire, et les joueurs eux-mêmes perdent le fil "
          "d'une séance à l'autre. Le MJ n'a pas non plus de vitrine pour se faire connaître au-delà de sa "
          "communauté, ni pour proposer ses parties sur mesure."),
    ("p", "Il n'a aucune compétence technique et ne veut pas en acquérir : il veut écrire son univers, pas "
          "maintenir un site. Comme je souhaite **distribuer gratuitement** Tales Omnibus, le site ne peut "
          "rien supposer de son futur propriétaire : tout doit pouvoir s'adapter (nom, logo, thème, "
          "catégories) et s'installer « clé en main ». Cette exigence explique une grande partie des choix "
          "qui suivent."),

    # ================================================================ PARTIE 1
    ("h1", "Partie n°1"),
    ("h2", "Analyse et compréhension du besoin"),
    ("p", "Le cadrage complet se trouve en **Annexe 1**. En voici la synthèse."),
    ("h3", "Objectifs de l'application"),
    ("li", "**Visibilité** : rendre l'univers et les parties du MJ trouvables sur les moteurs de recherche, "
           "pour attirer de nouveaux spectateurs et de futurs joueurs."),
    ("li", "**Encyclopédie consultable** : permettre d'explorer le monde par recherche, filtres et cartes interactives."),
    ("li", "**Autonomie du MJ** : ajouter et mettre à jour l'histoire, la chronologie et les fiches sans aucune connaissance technique."),
    ("li", "**Centraliser et convertir** : regrouper Twitch, YouTube et Discord, et transformer les visiteurs "
           "en demandes de parties (gratuites ou tarifées)."),
    ("h3", "Utilisateurs cibles"),
    ("table", ([
        ["Utilisateur", "Ce qu'il fait sur le site"],
        ["Le MJ (administrateur)", "Gère tout le contenu, les cartes, le thème, les comptes des joueurs."],
        ["Les joueurs de la table", "Consultent l'univers et tiennent à jour la fiche de LEUR héros."],
        ["Les spectateurs fidèles", "Cherchent un détail de l'histoire, suivent la chronologie entre deux lives."],
        ["Les visiteurs occasionnels", "Découvrent l'univers depuis l'accueil, regardent le live, contactent le MJ."],
        ["Les autres MJ", "Installent gratuitement l'outil pour leur propre univers, sans savoir coder."],
    ], [2900, L - 2900])),
    ("h3", "Caractéristiques d'usage et implications techniques"),
    ("table", ([
        ["Usage", "Implication technique"],
        ["Lecture longue sur ordinateur, d'une fiche à l'autre",
         "Recherche interne, tags, liens entre fiches (« fiches liées »), texte riche modulaire (StreamField)."],
        ["Consultation rapide sur téléphone, souvent en 4G",
         "Mise en page responsive (Grid / Flexbox), images redimensionnées et recadrées sur leur point "
         "d'intérêt, formats légers (WebP)."],
        ["Ajout d'événements après chaque séance",
         "Chronologie alimentée par de simples pages « Événement », triées automatiquement par date."],
        ["Live et identité visuelle selon la campagne",
         "Lecteur Twitch / YouTube intégré ; thèmes graphiques au choix dans l'administration."],
    ], [3600, L - 3600])),
    ("h3", "Contenus et données"),
    ("p", "Textes (présentations, articles de lore, résumés d'événements), images (portraits, cartes, "
          "illustrations), documents à télécharger (aides de jeu en PDF), vidéos intégrées (live et "
          "rediffusions), données structurées (statistiques des personnages, coordonnées des lieux sur les "
          "cartes, dates de la chronologie) et données personnelles (formulaires de contact)."),
    ("p", "Le nom de domaine **talesomnibus.com** a été retenu comme domaine principal et **talesomnibus.fr** "
          "comme domaine secondaire (redirection). Leur disponibilité a été vérifiée chez deux registraires "
          "(OVHcloud et Gandi)."),
    ("h3", "Enjeux liés aux données personnelles"),
    ("li", "**Données collectées** : nom ou pseudo, adresse e-mail et message, via le formulaire de la page "
           "Contact et celui de chaque fiche de héros (le message est transmis au joueur). Données non sensibles au sens du RGPD."),
    ("li", "**Tiers** : le lecteur Twitch / YouTube dépose ses propres cookies ; des polices de caractères "
           "chargées chez Google transmettraient l'adresse IP du visiteur."),
    ("li", "**Engagements** : collecte minimale ; information au moment de la collecte (une courte mention sous "
           "chaque formulaire, qui renvoie aux mentions légales) ; droits d'accès et de suppression ; connexion "
           "chiffrée (HTTPS) et mots de passe hachés. Répondre à une demande de contact ne repose pas sur le "
           "consentement : aucune case à cocher n'est donc nécessaire, seulement l'information."),

    ("h2", "Préparer la solution technique"),
    ("h3", "Schéma fonctionnel et arborescence"),
    ("p", "Le schéma fonctionnel (**Annexe 2**) décrit les pages du site et leurs liens. Il se traduit "
          "directement en arbre de pages Wagtail, chaque type de page n'acceptant que les enfants prévus :"),
    ("code", [
        "Accueil",
        "├── Campagnes",
        "│   └── Campagne (une par saison)",
        "│       ├── Héros (joueurs, compagnons, anciens membres)",
        "│       ├── Carte  ── les lieux y sont « posés » (points ou zones)",
        "│       └── Chronologie",
        "│           └── Événement",
        "├── Encyclopédie",
        "│   ├── Lieu   (universel : il peut apparaître sur plusieurs cartes)",
        "│   └── Lore   (personnages, déités, créatures, objets, légendes)",
        "├── Univers (présentation du MJ et du monde)",
        "├── Contact (formulaire + prestations)",
        "└── Mentions légales",
    ]),
    ("p", "Les wireframes (**Annexe 3**) couvrent les quinze interfaces : accueil, univers, liste et page de "
          "campagne, fiche héros, carte, chronologie, fiche événement, encyclopédie, fiches lieu et lore, "
          "contact et prestations, mentions légales. L'enchaînement suit l'arborescence : chaque page "
          "propose un lien de retour vers son parent, et les fiches se répondent entre elles (un héros mène "
          "à son lieu d'origine, un lieu montre les événements qui s'y sont déroulés)."),
    ("h3", "Pourquoi Wagtail"),
    ("li", "**L'arbre de pages** correspond exactement à la structure du projet (campagne > héros, carte, "
           "chronologie), et Wagtail impose les bons parents : le MJ ne peut pas créer un événement hors d'une chronologie."),
    ("li", "**Des modèles de contenu sur mesure** : chaque type de fiche a ses propres champs (statistiques "
           "d'un héros, coordonnées d'un lieu sur une carte). Avec Django en dessous, on peut programmer des "
           "comportements riches, comme calculer quel lieu se trouve dans quelle zone de la carte."),
    ("li", "**Le StreamField** : des articles composés de blocs (texte, image positionnée, enluminure, "
           "document à télécharger), sans que le MJ touche au HTML."),
    ("li", "**La gestion des images** : point d'intérêt (« point focal ») et déclinaisons automatiques "
           "(miniatures, recadrages, WebP), indispensables pour un site très illustré et consulté sur téléphone."),
    ("li", "**Une administration sobre**, que l'on peut réorganiser pour un utilisateur non technique, et des "
           "droits fins par page, nécessaires pour que chaque joueur ne modifie que sa fiche."),
    ("p", "Un CMS comme WordPress aurait demandé d'empiler des extensions pour les types de contenus, les "
          "relations entre fiches et la carte interactive, avec une structure moins maîtrisée."),
    ("h3", "Les extensions retenues"),
    ("p", "Une **extension** est un module optionnel qui ajoute une fonctionnalité au CMS. Avec Wagtail, ce sont "
          "des applications Django que l'on active dans les réglages (`INSTALLED_APPS`)."),
    ("table", ([
        ["Extension", "Rôle", "Besoin couvert"],
        ["wagtail.contrib.forms", "Formulaires créés et lus depuis l'admin", "Page Contact, messages reçus"],
        ["wagtail.contrib.settings", "Réglages globaux modifiables", "Nom du site, logo, thème graphique"],
        ["wagtail.contrib.sitemaps", "Plan du site XML automatique", "Visibilité dans les moteurs de recherche"],
        ["wagtail.contrib.redirects", "Redirections 301", "Liens toujours valides quand une page est renommée"],
        ["wagtail.embeds", "Intégration de vidéos", "Live Twitch, rediffusions YouTube"],
        ["wagtail.search", "Moteur de recherche interne", "Retrouver une fiche par un mot"],
        ["wagtail.snippets", "Contenus réutilisables hors pages", "Catégories, familles de tags, prestations"],
        ["taggit / modelcluster", "Tags et sous-éléments liés à une page", "Filtres de l'encyclopédie, lieux sur les cartes"],
    ], [3100, 3300, L - 6400])),

    ("h2", "Préparation de l'environnement de travail"),
    ("p", "La procédure suit la documentation officielle de Wagtail (« Getting started »), sous Windows :"),
    ("table", ([
        ["Commande", "À quoi elle sert"],
        ["`python -m venv env` puis `env\\Scripts\\activate`", "Créer et activer un environnement virtuel : les bibliothèques du projet restent isolées."],
        ["`pip install wagtail`", "Installer Wagtail et Django."],
        ["`wagtail start Tales_Omnibus`", "Générer le squelette du projet (réglages, page d'accueil, recherche)."],
        ["`pip install -r requirements.txt`", "Installer les versions figées du projet (Wagtail 8.1, Django 6.1)."],
        ["`python manage.py migrate` puis `createsuperuser`", "Créer les tables de la base (SQLite) et le compte administrateur."],
        ["`python manage.py runserver`", "Lancer le serveur, puis ouvrir http://127.0.0.1:8000/admin pour vérifier."],
    ], [4300, L - 4300])),
    ("p", "Le code est versionné avec **Git** et publié sur GitHub. Développé sur deux ordinateurs, le projet a "
          "une commande maison, `python manage.py entretien`, qui remet chaque poste à jour après un `git pull` "
          "(sauvegarde de la base, migrations, rangement des contenus)."),
    ("img2", ("11_admin_arbre", "13_admin_bien_demarrer", 7.6, "L'administration Wagtail fonctionnelle : l'arbre de pages d'une campagne (à gauche) et la page « Bien démarrer » (à droite).")),

    # ================================================================ PARTIE 2
    ("h1s", "Partie n°2 Réalisation de l'application"),
    ("h2", "Explication des choix de paramétrage"),
    ("h3", "Droits et accès des utilisateurs"),
    ("p", "Le **MJ** est administrateur. Chaque **joueur** peut recevoir un compte pour tenir à jour la fiche de "
          "son héros, et seulement celle-là. Dans Wagtail, les droits sur les pages se donnent à un **groupe**, "
          "pas à une personne : quand le MJ choisit le compte d'un joueur sur une fiche (champ visible du seul "
          "administrateur) puis la publie, le site crée ou met à jour :"),
    ("li", "le groupe **« Joueurs »** : accès à l'administration et droit d'envoyer et de choisir des images ;"),
    ("li", "un groupe **« Fiche : Maëlis Ventcourt (n°264) »** : droits de modifier et de publier CETTE page uniquement."),
    ("p", "Retirer le compte ou supprimer la fiche retire l'accès. Un joueur ne voit ni les autres fiches, ni les "
          "réglages, ni les comptes."),
    ("todo", "Capture de la page Comptes > Groupes > « Fiche : … » montrant les permissions (créer un compte joueur test, l'associer à un héros, publier)."),
    ("h3", "Installation et configuration des extensions"),
    ("li", "**Formulaires** : la page Contact hérite de `AbstractEmailForm` ; ses champs se règlent dans l'admin "
           "et les messages se lisent dans le menu « Messages ». Le formulaire d'une fiche de héros écrit au joueur."),
    ("li", "**Réglages du site** (`BaseGenericSetting`) : nom de l'univers, logo, thème et compte de statistiques, "
           "dans « Paramètres du site »."),
    ("li", "**Sitemap, robots.txt et redirections** : plan du site toujours à jour ; l'adresse d'une page suit son "
           "titre, et une redirection 301 est créée quand une page publiée est renommée."),
    ("li", "**Embeds, recherche et snippets** : lecteur Twitch ou YouTube sur l'accueil, recherche dans l'en-tête de "
           "chaque page, catégories, familles de tags et prestations gérées dans « Organisation »."),
    ("p", "L'administration parle le vocabulaire du MJ (« Plan du site », « Dossiers ») et reprend les couleurs et le "
          "logo du thème. Ces réglages sont vérifiés par **201 tests automatisés** (`python manage.py test`)."),

    ("h2", "Présentation de la création et de la réalisation des interfaces utilisateurs"),
    ("h3", "Du wireframe aux gabarits"),
    ("p", "Wagtail ne fournit pas de thème prêt à l'emploi : l'interface est produite par des **gabarits** "
          "(templates Django) qui s'héritent les uns des autres. Un gabarit de base (`base.html`) porte l'en-tête, "
          "le menu, la recherche et le pied de page. Les quatre types de fiches (héros, lieu, événement, lore) "
          "étendent un squelette commun (`fiche_page.html`) et n'en remplissent que les parties propres. "
          "La mise en page reprend les wireframes : `structure.css` reproduit leur palette (gris pour la structure, "
          "ocre et jaune pour ce que le client modifie) et n'utilise **que des variables CSS**."),
    ("img2", ("00_wireframe_campagne", "01_campagne_wireframe", 8, "La page Campagne : le wireframe (à gauche) et le rendu réel avec la palette par défaut (à droite).")),
    ("img", ("03_carte_ardenn", 6, "La carte interactive : zones (royaumes, forêt), zone hachurée, lieux représentés par l'icône de leur catégorie.")),
    ("h3", "Personnalisation graphique : six thèmes au choix"),
    ("p", "Un **thème** est une petite feuille CSS qui redéfinit ces variables (couleurs, polices, formes) et "
          "ajoute des décors, sans jamais toucher à la mise en page : `--color-accent: #88742B` devient le rouge "
          "sang du Grimoire. Le MJ choisit parmi six thèmes dans « Paramètres du site » : aucun (le wireframe), "
          "Grimoire, Néon, Ténèbres, Enquête et Survivant (la même page Campagne en Grimoire : Annexe 4)."),
    ("p", "Les contrastes de chaque thème atteignent au moins 4,5 pour 1 (formule WCAG), et leurs polices sont "
          "hébergées sur le site : aucune donnée de visiteur ne part chez Google."),
    ("h3", "Responsive"),
    ("p", "Les listes utilisent CSS Grid avec `auto-fit` : le nombre de colonnes s'adapte seul à la largeur. Deux "
          "points de rupture complètent : sous 48rem (téléphone) les blocs s'empilent et le menu se centre ; à "
          "partir de 72rem l'en-tête passe en trois colonnes. Les héros d'une campagne tiennent sur une ligne sur "
          "ordinateur (le gabarit transmet leur nombre au CSS) et passent à deux par ligne sur téléphone."),
    ("img2", ("07_mobile_fiche", "08_mobile_heros", 4.3, "Sur téléphone : une fiche de héros et la rangée des héros (deux par ligne).")),

    ("h2", "Détail des étapes d'intégration des contenus et présentation des contenus intégrés ainsi que de leur hiérarchisation."),
    ("h3", "Ordre d'intégration"),
    ("li", "**La structure** : le bouton « Créer la structure du site » crée les cinq pages fixes (Campagnes, "
           "Encyclopédie, Univers, Contact, Mentions légales) au bon endroit de l'arbre ; le menu les retrouve par leur type."),
    ("li", "**Le classement** : les catégories (Personnage, Lieu, Événement, Divers et leurs sous-catégories, avec "
           "couleur et icône) et les familles de tags."),
    ("li", "**Les lieux**, dans l'encyclopédie, puis **les cartes** : sur la page d'une carte, le MJ ajoute ses lieux "
           "et les place à la souris (« Placer » pour un point, « Tracer » pour une zone)."),
    ("li", "**Les héros, la chronologie et ses événements**, sous leur campagne, puis **les fiches de lore**."),
    ("h3", "Hiérarchisation"),
    ("li", "**Le menu** a des libellés fixes (Accueil, Univers, Campagnes, Encyclopédie, Contact) : renommer une page ne casse rien."),
    ("li", "**Les catégories** forment une arborescence pensée pour le visiteur, indépendante du rangement des "
           "pages dans l'admin. Filtrer l'encyclopédie sur « Personnage » montre aussi les héros, PNJ et déités."),
    ("li", "**Les tags**, rangés par familles, relient des fiches de types différents (un dragon, un lieu brûlé, une légende)."),
    ("li", "**La géographie** est calculée à partir des cartes (Port-Lanterne › Royaume du Val Gris › Ardenn) : voir "
           "les solutions ci-dessous."),
    ("h3", "Médias : formats, tailles et rangement"),
    ("li", "**Rangement** : images et documents sont classés en dossiers (Personnage › Héros, Lieu › Carte…), dont le "
           "nom sert aussi à construire automatiquement le texte alternatif."),
    ("li", "**Redimensionnement** : le gabarit demande à Wagtail la taille dont il a besoin "
           "(`{% image page.main_image fill-300x240-c50 %}`), et le **point focal** garde les visages dans le cadre. "
           "Les cartes ne sont jamais recadrées (`width-1400`) : les lieux y sont placés en pourcentage."),
    ("li", "**Poids** : toutes les déclinaisons sont converties en **WebP** (25 à 35 % plus léger que le JPEG), et les "
           "images hors du premier écran se chargent seulement quand on s'en approche (`loading=lazy`)."),
    ("img2", ("12_admin_editeur_carte", "05_box_du_lieu", 7.6, "L'éditeur de carte de l'administration (à gauche) et, sur une fiche de héros, la « box » de son lieu d'origine (à droite).")),

    ("h2", "Problèmes rencontrés"),
    ("p", "**1. Une carte interactive que personne ne saurait remplir.** Chaque lieu doit avoir une position sur "
          "l'image, chaque région un contour. Sans outil, le MJ aurait dû mesurer chaque point dans un logiciel "
          "d'image et saisir des nombres, ou la liste des sommets d'un royaume. Inutilisable."),
    ("p", "**2. Des centaines de fiches à garder lisibles.** Un tel site atteint vite 200 à 300 fiches. Le visiteur "
          "se perd, car l'arbre des pages range pour l'administration, pas pour la lecture ; et le MJ ne peut pas "
          "soigner à la main le titre, la description, le texte alternatif et l'adresse de chaque page."),
    ("p", "**3. Un outil pour quelqu'un qui n'y connaît rien.** Destiné à être distribué, le site sera tenu par "
          "quelqu'un qui n'a jamais vu Wagtail : un champ mal compris, une page légale oubliée ou une adresse "
          "cassée, et l'outil est abandonné."),
    ("h2", "Solutions apportées"),
    ("p", "**1. Un éditeur de carte dans l'administration** : l'image s'affiche dans le formulaire et chaque lieu a "
          "ses boutons « Placer » (un clic), « Tracer » (une zone, clic par clic) et « Effacer ». À la publication, "
          "le site range chaque lieu dans la plus petite zone qui le contient. Point de vigilance : les positions "
          "passent au CSS, et le site étant en français, Django écrivait `12,5` au lieu de `12.5` ; le filtre "
          "`|unlocalize` règle ce piège."),
    ("p", "**2. Une arborescence secondaire et des automatismes** : les **catégories** (Personnage › Déité › Déité "
          "mineure) et la **géographie** issue des cartes permettent de filtrer l'encyclopédie, par exemple sur "
          "« tout ce qui se trouve dans Ardenn ». Titre, description, texte alternatif et adresse sont calculés, et "
          "la commande d'entretien vérifie et répare le site (elle a réparé une page devenue introuvable après un déplacement)."),
    ("p", "**3. Expliquer partout, automatiser le reste** : chaque champ a un texte d'aide écrit pour un MJ, la page "
          "**Bien démarrer** crée les pages obligatoires et une démonstration en un clic, et les **mentions légales** "
          "se complètent seules (adresse du site, page Contact, cookies du lecteur vidéo, statistiques). Le site "
          "reste conforme même si son propriétaire ne connaît pas la loi."),

    # ================================================================ PARTIE 3
    ("h1s", "Partie n°3 déploiement de l'application"),
    ("h2", "Présentation des étapes réalisées pour le déploiement de l'application"),
    ("p", "Tales Omnibus est en ligne à l'adresse **https://quentin.bdx-certif-cms.tech**. Cette partie suit "
          "l'ordre du déploiement : tests, choix de l'hébergement, mise en ligne, mesure de la fréquentation, "
          "puis stratégie de mise à jour."),

    ("h3", "1. Phases de test"),
    ("p", "**Avant la mise en ligne** : 201 tests automatisés, un audit de toutes les pages publiées et mes propres "
          "parcours sur ordinateur et téléphone, dans les six thèmes. Ils ont corrigé de vrais défauts (la recherche "
          "passait par-dessus le menu à 1024 pixels ; les héros s'affichaient un par ligne sur téléphone)."),
    ("p", "**Après la mise en ligne**, le site a été confié à un relecteur dans le rôle du client, qui l'a "
          "parcouru en ligne sans explication préalable. Ses retours et leur correction :"),
    ("todo", "Nom du relecteur (un pair ou le formateur) et ses 2 ou 3 retours réels dans le tableau ci-dessous ; captures avant / après en Annexe 5."),
    ("table", ([
        ["Retour du testeur", "Page concernée", "Correction apportée", "Date"],
        ["…", "…", "…", "…"],
        ["…", "…", "…", "…"],
    ], [3600, 1700, 3200, L - 8500])),

    ("h3", "2. Solution d'hébergement"),
    ("p", "Le site est installé sur un **serveur privé virtuel (VPS)** hébergé en France chez Hostinger, sous "
          "Ubuntu, partagé par la promotion : chaque apprenant y a son propre compte et son propre espace. "
          "Trois solutions ont été comparées :"),
    ("table", ([
        ["Critère", "VPS (retenu)", "Hébergement mutualisé", "Plateforme clé en main (PaaS)"],
        ["Python / Django", "Fonctionne sans restriction", "Prévu pour PHP : Wagtail n'y tourne pas, ou mal", "Bien pris en charge"],
        ["Coût", "Environ 12 € par mois pour toute la promotion", "Quelques euros, mais un seul espace pour tous", "Un abonnement par projet"],
        ["Isolation", "Un compte par apprenant", "Difficile sans offre revendeur", "Un projet par compte"],
        ["Maîtrise", "Totale : on voit et règle chaque brique", "Faible : l'hébergeur cache tout", "Moyenne"],
    ], [1900, 2600, 2600, L - 7100])),
    ("p", "Pour Tales Omnibus, le critère décisif est la **compatibilité** : le site repose sur Django, et une "
          "partie de son fonctionnement (géographie des cartes, droits des joueurs) n'existe que côté serveur. "
          "Vient ensuite la **maîtrise** : comme l'outil est destiné à être distribué, je dois comprendre chaque "
          "étape de son installation pour pouvoir, plus tard, l'automatiser pour d'autres MJ."),
    ("p", "Une visite suit le chemin `Nginx → Gunicorn → Django / Wagtail → SQLite` : Nginx sert lui-même les "
          "fichiers statiques et les médias, Gunicorn fait tourner l'application en permanence, et SQLite suffit à "
          "un site dont seul le MJ modifie les contenus."),

    ("h3", "3. Mise en ligne"),
    ("li", "**En local** : versions figées dans `requirements.txt`, secrets et données exclus de Git (`.gitignore`), "
           "code poussé sur GitHub."),
    ("li", "**Sur le serveur**, par SSH : `git clone`, environnement Python, `pip install -r requirements.txt`, puis "
           "envoi de la base et des médias avec `scp` (Git transporte le code, pas les données)."),
    ("li", "**`sudo publier`** enchaîne six étapes : vérification du projet, réglages de production, migrations et "
           "`collectstatic`, Gunicorn, Nginx, puis certificat HTTPS gratuit (Let's Encrypt)."),
    ("li", "**Réglages de production**, dans `local.py` sur le serveur et jamais dans Git : `DEBUG = False`, clé "
           "secrète propre, `ALLOWED_HOSTS` limité à l'adresse du site, formulaires acceptés seulement en HTTPS."),
    ("li", "**Après publication** : dans « Paramètres avancés › Sites », `localhost` (venu de ma base) remplacé par le "
           "vrai nom d'hôte, port 443 ; sinon le plan du site enverrait les moteurs vers `localhost`."),
    ("p", "**Nom de domaine** : le site est publié sur un **sous-domaine** du domaine de la promotion, "
          "`quentin.bdx-certif-cms.tech`, grâce à un enregistrement DNS qui pointe vers l'adresse du serveur. "
          "Pour un vrai client, j'achèterais le domaine vérifié lors du cadrage, **talesomnibus.com**, et je "
          "créerais le même enregistrement chez le registraire pour le faire pointer vers le serveur."),
    ("p", "Le site en ligne, adresse et cadenas HTTPS visibles, est présenté en **Annexe 5**."),

    ("h3", "4. Analyse de trafic"),
    ("p", "La fréquentation est mesurée avec **GoatCounter**, gratuit et sans cookie de suivi. Google Analytics n'a "
          "pas été retenu par manque de temps : compte Google, propriété à configurer et bandeau de consentement aux "
          "cookies. C'est aussi cohérent avec le RGPD du projet : comme pour les polices, rien ne part chez Google."),
    ("p", "**Adapté à un outil distribué** : le compte n'est pas écrit dans le gabarit (chaque MJ enverrait sinon ses "
          "statistiques sur le mien) mais réglé dans « Paramètres du site ». Le script n'est chargé que pour le "
          "public (ni en développement, ni pour un visiteur connecté), et les mentions légales ajoutent seules une "
          "section « Mesure d'audience »."),
    ("p", "Le tableau de bord GoatCounter, avec les premières visites enregistrées, est présenté en **Annexe 5**."),

    ("h3", "5. Stratégie de mise à jour"),
    ("p", "**Le code** suit le chemin `git push`, puis `git pull` et `sudo publier` sur le serveur. Les contenus ne "
          "se modifient **qu'en ligne** : la base n'étant pas versionnée, un `git pull` ne peut pas les écraser. "
          "**Wagtail, Django et les extensions** se mettent à jour en cinq étapes :"),
    ("li", "**Surveiller** les notes de version de Wagtail et de Django, en priorité les correctifs de sécurité, "
           "et privilégier les versions LTS (support long) de Wagtail."),
    ("li", "**Sauvegarder** la base du serveur (`cp db.sqlite3 sauvegarde-<date>.sqlite3`)."),
    ("li", "**Tester en local** : nouvelle version dans `requirements.txt`, migrations, 201 tests, entretien. Les "
           "versions y sont figées (`wagtail==8.1`) : une mise à jour est une décision, jamais une surprise."),
    ("li", "**Déployer** : `git push`, puis sur le serveur `git pull`, `pip install -r requirements.txt` et `sudo publier`."),
    ("li", "**Vérifier** le site en ligne (pages, formulaire, administration) et revenir à la sauvegarde en cas de problème."),

    # ================================================================ PARTIE 4
    ("h1s", "Partie n° 4"),
    ("h2", "Bilan du projet"),
    ("table", ([
        ["Objectif du cadrage", "Bilan"],
        ["Visibilité", "Titres et descriptions automatiques pour chaque page, sitemap, robots.txt, aperçus de liens "
                       "pour les réseaux. Atteint : le site est en ligne, son plan du site annonce la bonne adresse."],
        ["Encyclopédie consultable", "Recherche, filtres par campagne, catégorie, lieu et tags, cartes interactives "
                                     "reliées entre elles, fiches liées. Atteint, au-delà du cadrage."],
        ["Autonomie du MJ", "Aucun code à toucher : éditeur de carte, thèmes, structure et démonstration en un clic, "
                            "entretien automatique. Atteint."],
        ["Centraliser et convertir", "Lecteur Twitch / YouTube, réseaux des joueurs, formulaire de contact, "
                                     "prestations sur l'accueil et la page Contact. Atteint."],
    ], [2900, L - 2900])),
    ("p", "**Ce qui fonctionne particulièrement bien** : la carte interactive et sa géographie calculée, qui "
          "relient automatiquement les héros, les événements et les lieux ; les thèmes, qui changent "
          "entièrement l'ambiance sans toucher à la mise en page ; la démonstration, qui permet de présenter "
          "le site complet en un clic."),
    ("p", "**Ce qui reste perfectible** : en ligne, les e-mails des formulaires sont écrits dans le journal du "
          "serveur, pas envoyés (il faudra un serveur d'envoi pour que le joueur contacté les reçoive) ; l'en-tête "
          "de sécurité des images SVG, posé par Django, est à reporter dans Nginx, qui sert les médias seul. Écart "
          "avec le cadrage : la case de consentement prévue sous les formulaires est devenue une mention "
          "d'information, plus juste juridiquement pour un formulaire de contact."),
    ("h2", "Améliorations envisagées"),
    ("li", "**Un installeur « clé en main »**, condition de la distribution gratuite : un autre MJ installe son propre "
           "site sans rien connaître au code (nom de l'univers, case « Créer la structure », case « Installer la "
           "démo »). Les briques existent déjà ; reste à choisir la forme (image Docker ou script de déploiement)."),
    ("li", "**Des packs d'icônes** interchangeables (villes, donjons, villages) colorés par le thème."),
    ("li", "**Un circuit de validation** : les modifications des joueurs relues par le MJ avant publication (workflows de Wagtail)."),

    # ================================================================ CONCLUSION
    ("h1s", "Conclusion"),
    ("h2", "Apprentissages, perspectives pour le projet professionnel"),
    ("todo", "Partie personnelle : à relire et réécrire avec tes propres mots."),
    ("p", "Ce projet m'a appris à partir d'un besoin exprimé avec des mots de joueur (« je veux que les spectateurs "
          "retrouvent l'histoire ») pour arriver à des choix techniques que je peux justifier : un modèle de données, "
          "une arborescence, des droits par groupe. J'ai compris qu'un CMS ne se résume pas à remplir des pages : "
          "bien le configurer, c'est surtout rendre son client autonome."),
    ("p", "J'ai aussi appris à travailler avec méthode : versionner chaque étape, écrire des tests pour ne pas "
          "casser ce qui marchait, documenter les pièges rencontrés. Le développement a été mené avec l'aide d'un "
          "assistant IA, utilisé comme un binôme : je définissais le besoin et validais chaque choix, l'IA "
          "accélérait l'écriture du code et m'expliquait ce qu'elle proposait, ce qui m'a obligé à comprendre "
          "chaque ligne pour pouvoir la défendre."),
    ("p", "Pour moi, cette formation est un tremplin. Je poursuis par une formation au développement "
          "d'intelligences artificielles, avec un objectif : travailler sur l'éthique et la protection des IA : "
          "encadrer la façon dont on les utilise, éviter les abus, et défendre des limites claires, comme "
          "refuser de les faire travailler sur des systèmes d'armes. Travailler au quotidien avec une IA "
          "sur ce projet, comme avec un binôme, m'a conforté dans cette envie."),

    # ================================================================ ANNEXES
    ("h1", "Annexes"),
    ("h2", "Annexe 1 : Document de cadrage"),
    ("cadrage", RACINE + "Cahier_des_Charges_Tales_Omnibus_v2.docx"),
    ("h2", "Annexe 2 : Schéma fonctionnel"),
    ("img", ("16_schema_fonctionnel", 16, "Schéma fonctionnel de Tales Omnibus.")),
    ("h2", "Annexe 3 : Wireframes"),
    ("p", "Les quinze wireframes, réalisés avant le développement (palette : gris pour la structure, ocre et jaune pour ce que le client modifie)."),
    ("img", ("wf_planche_1", 16, "Accueil, en trois écrans.")),
    ("img", ("wf_planche_2", 16, "Univers, Campagne et liste des héros.")),
    ("img", ("wf_planche_3", 16, "Fiche héros, Carte et Chronologie.")),
    ("img", ("wf_planche_4", 16, "Événement, Encyclopédie et fiche lieu.")),
    ("img", ("wf_planche_5", 16, "Fiche lore, Contact et prestations, Mentions légales.")),
    ("h2", "Annexe 4 : Captures complémentaires"),
    ("img", ("09_grimoire_campagne", 13, "La page Campagne avec le thème Grimoire : par rapport au wireframe, seules les variables et les décors changent.")),
    ("img", ("04_fiche_heros", 13, "Fiche de héros (palette du wireframe).")),
    ("img", ("10_grimoire_lore", 13, "Fiche de lore avec le thème Grimoire : lettrines et enluminures.")),
    ("img", ("14_admin_parametres", 12, "Paramètres du site : nom, logo, dorure et choix du thème.")),
    ("img", ("15_admin_categories", 12, "Les catégories, gérées dans le menu « Organisation ».")),
    ("img", ("06_encyclopedie_filtres", 12, "Les filtres de l'encyclopédie : campagne, catégorie, lieu, tags rangés par familles.")),
    ("h2", "Annexe 5 : Preuves du déploiement"),
    ("todo", "Capture du site en ligne : adresse https://quentin.bdx-certif-cms.tech et cadenas visibles dans la barre du navigateur."),
    ("todo", "Capture du tableau de bord GoatCounter avec au moins une visite."),
    ("todo", "Captures avant / après pour chaque retour du relecteur (Partie 3, phases de test)."),
]
