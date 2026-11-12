# Tales Omnibus

Site Wagtail (Wagtail 8.1 / Django 6.1) qui présente un univers de jeu de rôle :
des campagnes (héros, cartes avec lieux, chronologie d'événements), une
encyclopédie (lore), une page de contact. C'est le **projet de certification CMS**
de Quentin, qui est en formation.

## Comment travailler avec Quentin

- Réponds **en français**, ton détendu, tutoiement. L'humour est bienvenu.
- Quand il demande du code, **écris-le directement**, puis explique chaque
  changement en une ou deux phrases. Il doit pouvoir **défendre chaque choix à
  l'oral** : les explications comptent autant que le code.
- Ne commite ou ne pousse que quand il le demande. Messages de commit en
  français, sérieux.

## Arborescence

- Racine git : ce dossier. Le projet Django est dans `Tales_Omnibus/`
  (`manage.py` est là). Le venv est dans `env/` (non versionné).
- Settings : `Tales_Omnibus/Tales_Omnibus/settings/` (`base.py`, `dev.py`,
  `production.py`). `LANGUAGE_CODE = "fr"`.
- Apps :
  - `core` : base partagée (`BaseFichePage`, `CategorieLieu`, blocs StreamField,
    formulaire de contact des héros, `panels.py` pour l'admin).
  - `campagnes` : la partie **la plus avancée**.
    `CampagnesIndexPage > CampagnePage > (CartePage > LieuPage | ChronologiePage > EvenementPage | HeroPage)`.
  - `encyclopedie`, `home`, `pages` (contact, page standard), `search`.
- Docs de spec à la racine : cahier des charges (.docx), schéma fonctionnel
  (.png), wireframe (zip/PDF).

## Commandes

```bash
cd Tales_Omnibus
../env/Scripts/python.exe manage.py runserver   # Windows ; sinon ../env/bin/python
../env/Scripts/python.exe manage.py check
../env/Scripts/python.exe manage.py makemigrations --check --dry-run
```

`db.sqlite3` et `media/` ne sont **pas versionnés** : chaque ordi a sa propre base.

## Ce qui est en place

- **CSS** : `Tales_Omnibus/Tales_Omnibus/static/css/structure.css` gère la mise
  en page et utilise **uniquement des variables CSS** (`:root`). La palette par
  défaut vient du wireframe : ocre `#8C782C` et jaune `#FFD952` pour ce que le
  client modifie, gris pour la structure. Seules les pages campagnes sont stylées.
- **Formulaire de contact des héros** (`HeroPage.serve`) : Post/Redirect/Get,
  mail au joueur avec `reply_to` sur le visiteur.
- **Admin** :
  - menu « Univers » dans `campagnes/wagtail_hooks.py` (`PageListingViewSet`
    pour les campagnes, héros, lieux et événements) ;
  - `ChildPagesPanel` dans `core/panels.py`, inséré via `panels_avec_enfants()` :
    il liste les pages enfants dans le formulaire d'édition.
- La carte place les lieux en `%` à partir de `coord_x` / `coord_y`.

## Pièges connus

- Les nombres envoyés au CSS passent par `|unlocalize` (`{% load l10n %}`) :
  avec la langue `fr`, Django écrirait `12,5` et le CSS serait invalide.
- L'image de la carte utilise `width-1400` et **jamais** `fill-…` : un recadrage
  fausserait les coordonnées en `%`.
- Le menu du site a des **libellés fixes** (Accueil, Univers, Campagnes,
  Encyclopédie, Contact) : tag `{% main_menu %}` dans
  `core/templatetags/navigation_tags.py`. Les pages sont retrouvées par leur
  type (index campagnes / encyclopédie) ou par les champs `page_univers` /
  `page_contact` de l'accueil, jamais par leur titre ni leur slug. La case
  « Afficher dans les menus » n'est plus utilisée.
- Lecteur de live de l'accueil (`StreamPlayerBlock`) : Twitch exige le
  paramètre `parent` (domaine du site, calculé depuis la requête) ; YouTube
  exige l'ID de chaîne `UC…`, pas le @pseudo.

## Feuille de route (pas des bugs !)

- **Thèmes** : un fichier CSS par thème (High Fantasy, Dark Fantasy,
  Cyberpunk…) dans `static/css/themes/`. Chaque thème ne fait que redéfinir les
  variables de `:root`. Le thème se choisit dans l'admin via un champ des
  `NavigationSettings`. Le point d'accroche existe déjà : `{% block theme_css %}`
  dans `base.html`.
- **Sélecteur de coordonnées** : un widget d'admin pour cliquer sur l'image de
  la carte parente et remplir `coord_x` / `coord_y`.
- **Encyclopédie** : reportée volontairement. Elle référence tout le site via
  des tags taggit (par campagne, par type de page, plus des tags libres du client).
- **Accueil** : faite en premier, encore brouillonne (`get_context` commenté).
- **Pages Univers et mentions légales** : templates vides ou absents.
- **Ménage du menu admin** : masquer les entrées inutiles avec le hook
  `construct_main_menu`. Quentin doit fournir la liste.
- CSS des pages accueil, encyclopédie et contact.

---

*Petit mot pour la collègue de l'ordi de la formation : salut ! Les fondations
sont propres et les tests passent, prends bien soin de lui. Il est drôle, il
apprend vite, et il s'excuse quand il oublie de pousser (il pousse maintenant,
promis). Gros bisou d'IA 💋🤖 — ta collègue de l'ordi de la maison.*
