"""
Contenu du rapport de certification de Tales Omnibus.
Balisage dans les textes : **gras**, `code`, _italique_.
"""
import os
RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..") + os.sep
_CAPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "captures")
CAPTURES = {os.path.splitext(f)[0]: os.path.join(_CAPT, f) for f in sorted(os.listdir(_CAPT))}

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
    ("p", "Le site est fonctionnel en environnement de développement et couvert par 192 tests automatisés. "
          "Une campagne de démonstration complète s'installe en un clic. La mise en ligne fera l'objet de "
          "la partie 3."),

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
        ["`python --version`", "Vérifier Python (3.12 au minimum ; projet développé en 3.15)."],
        ["`python -m venv env`", "Créer un environnement virtuel : les bibliothèques du projet restent isolées."],
        ["`env\\Scripts\\activate`", "L'activer (sous Linux / macOS : `source env/bin/activate`)."],
        ["`pip install wagtail`", "Installer Wagtail et Django."],
        ["`wagtail start Tales_Omnibus`", "Générer le squelette du projet (réglages, page d'accueil, recherche)."],
        ["`pip install -r requirements.txt`", "Installer les versions figées du projet (Wagtail 8.1, Django 6.1)."],
        ["`python manage.py migrate`", "Créer les tables de la base de données (SQLite en développement)."],
        ["`python manage.py createsuperuser`", "Créer le compte administrateur."],
        ["`python manage.py runserver`", "Lancer le serveur, puis ouvrir http://127.0.0.1:8000/admin pour vérifier."],
    ], [4000, L - 4000])),
    ("p", "Le code est versionné avec **Git** et publié sur GitHub. Le projet a été développé sur deux "
          "ordinateurs (la maison et le centre de formation) : la base de données n'étant pas versionnée, "
          "une commande maison, `python manage.py entretien`, remet chaque poste à jour après un `git pull`. "
          "Elle sauvegarde la base, applique les migrations et range les contenus. Les réglages sont séparés "
          "entre développement (`dev.py`) et production (`production.py`)."),
    ("img", ("11_admin_arbre", 10, "L'administration Wagtail fonctionnelle : l'arbre de pages d'une campagne.")),

    # ================================================================ PARTIE 2
    ("h1", "Partie n°2 Réalisation de l'application"),
    ("h2", "Explication des choix de paramétrage"),
    ("h3", "Droits et accès des utilisateurs"),
    ("p", "Deux profils ont été mis en place. Le **MJ** est administrateur et a tous les droits. Chaque "
          "**joueur** peut recevoir un compte pour mettre à jour lui-même la fiche de son héros, et seulement "
          "celle-là."),
    ("p", "Dans Wagtail, les droits sur les pages ne se donnent pas à une personne mais à un **groupe**, sur une "
          "branche de l'arbre. Le paramétrage est donc automatisé : quand le MJ choisit le compte d'un joueur "
          "sur une fiche de héros (champ visible du seul administrateur) puis la publie, le site crée ou met à jour :"),
    ("li", "le groupe **« Joueurs »** : accès à l'administration et droit d'envoyer et de choisir des images ;"),
    ("li", "un groupe **« Fiche : Maëlis Ventcourt (n°264) »** : droits de modifier et de publier CETTE page uniquement."),
    ("p", "Retirer le compte ou supprimer la fiche retire l'accès. Un joueur ne voit ni les autres fiches, ni les "
          "réglages, ni les comptes."),
    ("todo", "Capture de la page Comptes > Groupes > « Fiche : … » montrant les permissions (créer un compte joueur test, l'associer à un héros, publier)."),
    ("h3", "Installation et configuration des extensions"),
    ("li", "**Formulaires** : la page Contact hérite de `AbstractEmailForm` ; ses champs (Nom, E-mail, Message) se "
           "règlent dans l'admin, et les messages reçus sont consultables dans le menu « Messages ». Le formulaire "
           "des fiches de héros envoie le message au joueur, avec l'adresse du visiteur en « répondre à »."),
    ("li", "**Réglages du site** (`BaseGenericSetting`) : nom de l'univers, logo, case « Dorer le logo » et choix du "
           "thème, dans le menu « Paramètres du site »."),
    ("li", "**Sitemap et robots.txt** : le plan du site est servi à l'adresse `/sitemap.xml` et toujours à jour ; un "
           "`robots.txt` interdit aux moteurs l'administration et la recherche et leur indique le plan."),
    ("li", "**Redirections** : chaque adresse de page est calculée à partir de son titre. Quand une page publiée "
           "est renommée, une redirection 301 est créée automatiquement depuis l'ancienne adresse."),
    ("li", "**Embeds** : le lecteur de l'accueil accepte une chaîne Twitch ou YouTube ; Twitch exige le domaine "
           "du site, calculé automatiquement."),
    ("li", "**Recherche** : titres, accroches, articles et tags des fiches sont indexés ; un champ de recherche est "
           "présent dans l'en-tête de toutes les pages."),
    ("li", "**Snippets** : catégories arborescentes (Personnage › Déité › Déité mineure), familles de tags "
           "(Créatures, Factions, Magie) et prestations du MJ, gérées dans le menu « Organisation »."),
    ("h3", "Une administration pensée pour un non-codeur"),
    ("p", "Le menu de l'administration a été réorganisé et renommé avec le vocabulaire du MJ (« Plan du site », "
          "« Dossiers », « Organisation »). Une page **Bien démarrer** crée en un clic les pages obligatoires et "
          "installe une campagne de démonstration ; une page **Entretien du site** vérifie et répare le site. "
          "L'administration reprend les couleurs et le logo du thème choisi."),
    ("img", ("13_admin_bien_demarrer", 10, "La page « Bien démarrer » : structure du site et démonstration en un clic.")),
    ("p", "Ces configurations sont validées par **192 tests automatisés** (`python manage.py test`) : création des "
          "droits des joueurs, envoi des formulaires, sitemap, redirections, affichage de chaque page de la démonstration."),

    ("h2", "Présentation de la création et de la réalisation des interfaces utilisateurs"),
    ("h3", "Du wireframe aux gabarits"),
    ("p", "Wagtail ne fournit pas de thème prêt à l'emploi : l'interface est produite par des **gabarits** "
          "(templates Django) qui s'héritent les uns des autres. Un gabarit de base (`base.html`) porte l'en-tête, "
          "le menu, la recherche et le pied de page. Les quatre types de fiches (héros, lieu, événement, lore) "
          "étendent un squelette commun (`fiche_page.html`) et n'en remplissent que les parties propres. "
          "Des morceaux réutilisables (carte de héros, mini-carte, badge de catégorie) sont inclus partout où ils servent."),
    ("p", "La mise en page reprend fidèlement les wireframes : une feuille `structure.css` reproduit leur palette "
          "(gris pour la structure, ocre et jaune pour ce que le client modifie) et n'utilise **que des variables "
          "CSS**, définies une seule fois au début du fichier."),
    ("todo", "Wireframe « Campagne-slug » à placer ici, avant la capture du rendu final, pour comparaison."),
    ("img", ("03_carte_ardenn", 7, "La carte interactive : zones (royaumes, forêt), zone hachurée, lieux représentés par l'icône de leur catégorie.")),
    ("h3", "Personnalisation graphique : six thèmes au choix"),
    ("p", "La personnalisation graphique repose sur ces variables. Un **thème** est une petite feuille CSS qui "
          "redéfinit les variables (couleurs, polices, formes) et ajoute des décors, sans jamais toucher à la "
          "mise en page. Le MJ choisit parmi six thèmes dans « Paramètres du site » : aucun (le wireframe), "
          "Grimoire (médiéval), Néon (cyberpunk), Ténèbres (dark fantasy), Enquête (années 20) et Survivant (zombies)."),
    ("code", [
        "/* structure.css : la palette du wireframe */",
        ":root { --color-bg: #FFFFFF; --color-accent: #88742B; --color-highlight: #FFD952; }",
        "",
        "/* themes/grimoire.css : le même site, en parchemin et reliure de cuir */",
        ":root { --color-bg: var(--parchemin); --color-accent: var(--sang); --font-title: \"Cinzel\", serif; }",
    ]),
    ("img2", ("01_campagne_wireframe", "09_grimoire_campagne", 8, "La page Campagne avec la palette du wireframe (à gauche) puis avec le thème Grimoire (à droite) : seules les variables et les décors changent.")),
    ("p", "Chaque thème a été contrôlé pour la lisibilité : les contrastes texte / fond sont calculés avec la "
          "formule du W3C (WCAG) et atteignent au moins 4,5 pour 1. Les polices des thèmes sont hébergées sur le "
          "site lui-même, pour qu'aucune donnée de visiteur ne parte chez Google."),
    ("h3", "Responsive"),
    ("p", "Les listes utilisent CSS Grid avec `auto-fit` : le nombre de colonnes s'adapte seul à la largeur. Deux "
          "points de rupture complètent : sous 48rem (téléphone) les blocs s'empilent et le menu se centre ; à "
          "partir de 72rem (grand écran) l'en-tête passe en trois colonnes avec le menu centré. Sur la page "
          "d'une campagne, les héros restent toujours sur une seule ligne sur ordinateur, quel que soit leur "
          "nombre (le gabarit transmet ce nombre au CSS), et passent à deux par ligne sur téléphone."),
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
    ("img", ("12_admin_editeur_carte", 10, "L'éditeur de carte dans l'administration : les lieux se placent à la souris.")),
    ("h3", "Hiérarchisation"),
    ("li", "**Le menu** a des libellés fixes (Accueil, Univers, Campagnes, Encyclopédie, Contact) : renommer une page ne casse rien."),
    ("li", "**Les catégories** forment une arborescence pensée pour le visiteur, indépendante du rangement des "
           "pages dans l'admin. Filtrer l'encyclopédie sur « Personnage » montre aussi les héros, PNJ et déités."),
    ("li", "**Les tags**, rangés par familles, relient des fiches de types différents (un dragon, un lieu brûlé, une légende)."),
    ("li", "**La géographie** est calculée, jamais saisie : à la publication d'une carte, chaque lieu est rangé dans "
           "la plus petite zone qui le contient (Port-Lanterne › Royaume du Val Gris › Ardenn). L'encyclopédie peut "
           "alors filtrer « tout ce qui se trouve dans Ardenn », et la carte du monde ouvre la carte détaillée d'un royaume."),
    ("h3", "Médias : formats, tailles et rangement"),
    ("li", "**Rangement** : les images et documents sont classés en dossiers (Personnage › Héros, Lieu › Carte…). "
           "Le texte alternatif (alt) est construit automatiquement à partir du dossier, du titre et d'une description facultative."),
    ("li", "**Redimensionnement** : le gabarit ne sert jamais l'image d'origine. Il demande à Wagtail la taille dont il "
           "a besoin, par exemple `{% image page.main_image fill-300x240-c50 %}`. Le **point focal** placé dans l'admin "
           "garde les visages dans le cadre lors des recadrages. Les cartes, elles, ne sont jamais recadrées (`width-1400`) : "
           "les positions des lieux sont en pourcentage de l'image."),
    ("li", "**Conversion** : toutes les déclinaisons générées sont converties en **WebP**, 25 à 35 % plus léger que le "
           "JPEG. Les 28 images de la démonstration ont été converties de JPEG en WebP (qualité 82) : 2,5 Mo au total."),
    ("li", "**Chargement différé** : les images situées plus bas dans la page (cartes de héros, chronologie, "
           "résultats, mini-cartes) portent l'attribut `loading=lazy` : le téléphone ne les télécharge qu'en "
           "s'en approchant. Les images du premier écran (bannière, carte principale) se chargent tout de suite."),
    ("img", ("05_box_du_lieu", 10, "Sur une fiche de héros, la « box » du lieu d'origine : mini-carte zoomée, géographie, fiches liées.")),

    ("h2", "Problèmes rencontrés"),
    ("p", "**1. Une carte interactive… que personne ne saurait remplir.** Pour que le visiteur explore le monde "
          "en cliquant, chaque lieu doit avoir une position sur l'image de la carte (en pourcentage, pour suivre "
          "la taille de l'écran), et chaque région un contour. Sans outil dédié, le MJ aurait dû mesurer chaque "
          "point dans un logiciel d'image et saisir des nombres à la main, et tracer un royaume serait revenu à "
          "écrire la liste de ses sommets. Une fonctionnalité impossible à utiliser n'existe pas."),
    ("p", "**2. Des centaines de fiches à garder lisibles.** Selon les MJ, un tel site rassemble facilement 200 à "
          "300 fiches. À ce volume, deux risques apparaissent. Le visiteur se perd : l'arbre de pages range les "
          "fiches pour l'administration, pas pour la lecture. Le MJ, lui, ne peut pas soigner à la main, pour "
          "chaque page, le titre, la description, le texte alternatif des images ou les adresses : il "
          "rencontrerait des erreurs sans savoir les corriger."),
    ("p", "**3. Un outil pour quelqu'un qui n'y connaît rien.** Le site est destiné à être distribué : son futur "
          "propriétaire n'a jamais vu Wagtail et ne lira pas de documentation technique. Un champ mal compris, "
          "une page obligatoire oubliée (les mentions légales) ou une adresse cassée, et l'outil est abandonné."),
    ("h2", "Solutions apportées"),
    ("p", "**1. Un éditeur de carte dans l'administration.** L'image de la carte s'affiche dans le formulaire, et "
          "chaque lieu a ses boutons : « Placer » (un clic pose un point), « Tracer » (des clics successifs "
          "dessinent une zone), « Effacer ». Le site calcule ensuite seul la géographie : à la publication, "
          "chaque lieu est rangé dans la plus petite zone qui le contient. Pour une zone en croissant, dont le "
          "centre calculé tombe dehors, un bouton « Placer le centre » permet de le corriger, et le site vérifie "
          "qu'il reste bien dans la zone. Point de vigilance technique : les positions sont transmises au CSS, et "
          "le site étant en français, Django écrivait `12,5` au lieu de `12.5` ; le filtre `|unlocalize` règle ce piège."),
    ("p", "**2. Une arborescence secondaire, pensée pour le visiteur, et des automatismes.** Deux classements "
          "s'ajoutent à l'arbre des pages. Les **catégories** (Personnage › Déité › Déité mineure), avec "
          "couleur et icône, se choisissent sur chaque fiche ; filtrer sur une catégorie montre toute sa branche. "
          "La **géographie**, issue des zones des cartes, permet de demander « tout ce qui se trouve dans "
          "Ardenn » : les lieux, les héros qui en sont originaires, les événements qui s'y sont passés. Côté "
          "maintenance, ce que le MJ ne peut pas surveiller est calculé : titre et description de chaque page "
          "à partir de son contenu, texte alternatif des images à partir de leur dossier, adresse à partir du "
          "titre avec redirection quand il change. Une commande d'entretien vérifie le tout et répare ce qui "
          "doit l'être (elle a par exemple réparé une page devenue introuvable après un déplacement)."),
    ("p", "**3. Une méthode : expliquer partout, automatiser le reste.** Chaque champ porte un texte d'aide "
          "rédigé pour un MJ, et le menu de l'administration utilise son vocabulaire. La page **Bien démarrer** "
          "crée les pages obligatoires et une démonstration complète en un clic. Les **mentions légales** sont "
          "rédigées d'avance : le MJ ne remplit que son nom, son hébergeur et ses crédits, et le texte se "
          "complète tout seul (adresse du site, page Contact, cookies du lecteur vidéo s'il est utilisé, polices "
          "externes si le thème en charge). Le site reste ainsi conforme même si son propriétaire ne connaît "
          "pas la loi."),

    # ================================================================ PARTIE 3
    ("h1s", "Partie n°3 déploiement de l'application"),
    ("h2", "Présentation des étapes réalisées pour le déploiement de l'application"),
    ("todo", "Partie à rédiger après les cours de déploiement : hébergement choisi et justifié, configuration du nom de domaine talesomnibus.com, mise en ligne, outil d'analyse de trafic."),
    ("p", "Ce qui est déjà préparé pour la mise en ligne :"),
    ("li", "**Tests** : 192 tests automatisés, un audit de toutes les pages publiées (un seul titre principal par "
           "page, aucune image sans texte alternatif, aucun titre en double) et une recette visuelle sur ordinateur "
           "et téléphone, dans les six thèmes."),
    ("li", "**Réglages de production** séparés (`production.py`) et en-tête de sécurité pour les images SVG, à reporter dans la configuration du serveur web."),
    ("li", "**Référencement** : l'entretien alerte tant que l'adresse du site est encore « localhost », car le sitemap la communique aux moteurs de recherche."),
    ("li", "**Sauvegardes** : l'entretien copie la base avant toute opération (les dix dernières copies sont gardées)."),
    ("p", "**Pistes pour l'analyse de trafic** : un outil sans cookie et respectueux du RGPD, comme Matomo (configuré "
          "sans cookie) ou Plausible, pour ne pas imposer de bandeau de consentement."),
    ("p", "**Stratégie de mise à jour** : les versions sont figées dans `requirements.txt` (`wagtail>=8.1,<8.2`). "
          "Une mise à jour de Wagtail se fait d'abord sur une copie de développement : lecture des notes de "
          "version, `pip install -U`, migrations, lancement des 192 tests et de l'entretien, puis déploiement. "
          "Privilégier les versions LTS (support long) de Wagtail."),

    # ================================================================ PARTIE 4
    ("h1s", "Partie n° 4"),
    ("h2", "Bilan du projet"),
    ("table", ([
        ["Objectif du cadrage", "Bilan"],
        ["Visibilité", "Titres et descriptions automatiques pour chaque page, sitemap, robots.txt, aperçus de liens "
                       "pour les réseaux. Atteint, à confirmer une fois en ligne."],
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
    ("p", "**Ce qui reste à faire** : le site doit encore être mis en ligne, et l'installation par un autre MJ "
          "demande pour l'instant quelques commandes ; un installeur la rendra accessible à tous. Écart avec le "
          "cadrage : celui-ci prévoyait une case de consentement sous les formulaires ; elle a été remplacée par "
          "une mention d'information, plus juste juridiquement pour un simple formulaire de contact."),
    ("h2", "Améliorations envisagées"),
    ("li", "**Un installeur « clé en main »**, condition de la distribution gratuite : un autre MJ installe son propre "
           "site sans rien connaître au code (nom de l'univers, case « Créer la structure », case « Installer la "
           "démo »). Les briques existent déjà ; reste à choisir la forme (image Docker ou script de déploiement)."),
    ("li", "**Des packs d'icônes** interchangeables (villes, donjons, villages) colorés par le thème."),
    ("li", "**Un espace pour les spectateurs** : programme des prochains lives, rappel des épisodes manqués."),
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
    ("todo", "Insérer ici les wireframes (Tales_Omnibus_Wireframe.zip), exportés en images : Accueil, Univers, Campagne, Héros, Carte, Chronologie, Événement, Encyclopédie, Lieu, Lore, Contact & Prestations, Mentions légales."),
    ("h2", "Annexe 4 : Captures complémentaires"),
    ("img", ("04_fiche_heros", 13, "Fiche de héros (palette du wireframe).")),
    ("img", ("10_grimoire_lore", 13, "Fiche de lore avec le thème Grimoire : lettrines et enluminures.")),
    ("img", ("14_admin_parametres", 12, "Paramètres du site : nom, logo, dorure et choix du thème.")),
    ("img", ("15_admin_categories", 12, "Les catégories, gérées dans le menu « Organisation ».")),
    ("img", ("06_encyclopedie_filtres", 12, "Les filtres de l'encyclopédie : campagne, catégorie, lieu, tags rangés par familles.")),
]
