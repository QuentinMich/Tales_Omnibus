# Images de la démo « Les Brumes d'Ardenn »

Les fichiers de ce dossier sont importés dans la médiathèque quand on installe
la démo (bouton **Ajouter la démo** de la page **Bien démarrer** dans l'admin, ou
`manage.py creer_demo`). Chaque image est **rangée dans son dossier**, avec son
titre et sa description : l'ALT automatique est donc propre, et le nouveau MJ voit
un vrai exemple de médiathèque bien tenue. Retirer la démo retire aussi ces images.

**Il manque un fichier ?** Pas grave : la démo réutilise les images déjà présentes
sur le site, à tour de rôle. Tu peux donc les ajouter petit à petit.

## Comment déposer une image

1. Nomme le fichier **exactement** comme dans la colonne « Fichier » (sans accent,
   en minuscules). Formats acceptés : `.jpg`, `.jpeg`, `.png`, `.webp` ou `.svg`.
2. Dépose-le dans ce dossier (`core/donnees_demo/images/`).
3. Retire puis remets la démo (page **Bien démarrer**).

Le titre, le dossier et la description sont déjà déclarés dans `core/demo.py`
(dictionnaire `IMAGES`) : rien d'autre à remplir.

## Conseils pour un ensemble cohérent

- **Un même style pour toutes les images** (même outil, même « recette »), sinon la
  démo ressemble à un patchwork. Suggestion, à ajouter à chaque demande :
  *« digital painting, dark fantasy, misty atmosphere, muted earthy palette,
  soft volumetric light, painterly, no text, no watermark »*.
- **Le sujet au centre de l'image** : les fiches affichent l'image en portrait,
  les vignettes (chronologie, fiches liées) la recadrent en paysage. Un sujet bien
  centré survit aux deux recadrages. Le **point focal** de Wagtail (dans l'admin,
  sur chaque image) peut ensuite affiner.
- **Aucun texte dans les images** : les titres sont déjà sur le site, et un texte
  dans une image n'est lu ni par les lecteurs d'écran ni par les moteurs de recherche.
- **Les cartes** : style carte dessinée à la main, **sans noms écrits** (les noms des
  lieux sont posés par le site, et se traduisent / se modifient).
- **Format WebP**, qualité ~82 : les 28 images livrées pèsent 2,5 Mo en tout
  (21 Mo en JPG), sans différence visible. Le site d'un client se télécharge
  plus vite, et Wagtail fabrique lui-même les versions plus petites. Pour
  convertir : `Image.open(f).convert("RGB").save(f.with_suffix(".webp"), "WEBP", quality=82, method=6)`
  (Pillow, déjà installé avec Wagtail).

## La liste (28 images à générer)

Les 3 icônes de catégories (`icone-ville.svg`, `icone-village.svg`,
`icone-lieu-dit.svg`) sont **déjà là** : dessinées en SVG d'une seule couleur.

### La campagne et les cartes

| Fichier | Format | Dossier | Utilisée sur | Idée (prompt) |
|---|---|---|---|---|
| `banniere-brumes-ardenn` | paysage très large, 2400×860 | Site | bannière de la campagne | A vast misty continent at dusk seen from a hill, rolling hills and dark forests drowning in fog, tiny warm lanterns glowing in the distance |
| `carte-ardenn` | portrait, 1800×2400 | Lieu › Carte | page Carte d'Ardenn | Hand-drawn fantasy map on aged parchment, top-down view of a continent: coastline, a forest in the south-west, a burnt black plain in the north-east, a river, a port town, a ruined fortress, small lakes, compass rose, no labels, no text |
| `carte-val-gris` | portrait, 1800×2400 | Lieu › Carte | page Carte du Val Gris | Hand-drawn map on stained parchment of a hidden valley kingdom surrounded by grey fog and mountains, a few towers, a river, sketchy and unfinished like drawn by a survivor, no labels, no text |

### Les héros

Les héros joués par le MJ (compagnons de route) et ceux qui ont quitté le groupe sont
quand même des fiches Héros : leurs images vont dans **Personnage › Héros**.

| Fichier | Format | Dossier | Utilisée sur | Idée (prompt) |
|---|---|---|---|---|
| `heros-maelis-ventcourt` | portrait, 1200×1800 | Personnage › Héros | Maëlis Ventcourt | Portrait of a young female cartographer, ink-stained fingers, leather satchel full of rolled maps, holding a brass compass, windswept hair, misty cliffs behind |
| `heros-brann-le-rouquin` | portrait, 1200×1800 | Personnage › Héros | Brann le Rouquin | Portrait of a huge red-bearded woodcutter, flannel and fur, holding an old axe with a faint ghostly blue glow, slightly worried look, dark forest behind |
| `heros-pip-chardon` | portrait, 1200×1800 | Personnage › Héros | Pip Chardon | Portrait of a small halfling thief girl with a mischievous innocent smile, oversized hooded cloak, pockets bulging with stolen trinkets, lantern-lit harbour alley behind |
| `heros-soeur-ysolde` | portrait, 1200×1800 | Personnage › Héros (jouée par le MJ) | Sœur Ysolde | Portrait of a stern nun in a black habit, a raven perched on her shoulder, a small lantern in hand, half-smile, ruined fortress in the fog behind |
| `heros-gaspard-tetenoire` | portrait, 1200×1800 | Personnage › Héros (a quitté le groupe) | Gaspard Têtenoire | A grumpy mercenary in dented armour seen from behind, walking away alone on a misty road at dawn, sword on his shoulder |

### Les lieux

| Fichier | Format | Dossier | Utilisée sur | Idée (prompt) |
|---|---|---|---|---|
| `lieu-ardenn` | portrait, 1200×1700 | Lieu › Paysage | Ardenn | Misty landscape of hills and dark forests, roads disappearing into the fog, a lonely signpost |
| `lieu-royaume-du-val-gris` | portrait, 1200×1700 | Lieu › Paysage | Royaume du Val Gris | A hidden valley with slender stone towers, half-veiled by a curtain of magical grey fog |
| `lieu-port-lanterne` | portrait, 1200×1700 | Lieu › Ville | Port-Lanterne | A harbour town at night lit by hundreds of lanterns, all of them seemingly turned toward the viewer, reflections on dark water |
| `lieu-fort-sombre` | portrait, 1200×1700 | Lieu › Ville | Fort-Sombre | A ruined fortress on a rocky hill, crumbling walls covered with crows, grey stormy sky |
| `lieu-hameau-des-saules` | portrait, 1200×1700 | Lieu › Ville | Hameau des Saules | Three small cottages around a stone well, a huge weeping willow, gentle rain |
| `lieu-bois-des-murmures` | portrait, 1200×1700 | Lieu › Paysage | Bois des Murmures | An ancient dark forest with twisted trunks leaning toward each other as if whispering, faint mist between the trees |
| `lieu-terres-brulees` | portrait, 1200×1700 | Lieu › Paysage | Terres Brûlées | A scorched black plain, charred dead trees, ash in the air, faint embers on the ground |

### Le Lore (encyclopédie)

| Fichier | Format | Dossier | Utilisée sur | Idée (prompt) |
|---|---|---|---|---|
| `lore-vael-deesse-des-brumes` | portrait, 1200×1700 | Personnage › Déité | Vaël, déesse des Brumes | A goddess made of swirling mist, pale face, holding an extinguished lantern, ethereal and calm |
| `lore-kroth-le-petit` | portrait, 1200×1700 | Personnage › Déité | Kroth le Petit | A small pot-bellied god covered in dozens of key rings and old keys, mischievous grin, warm candlelight |
| `lore-lordre-du-corbeau` | portrait, 1200×1700 | Personnage › PNJ | L'Ordre du Corbeau | Knights in black armour with raven-feather cloaks, crows perched on their shoulders, standing in fog |
| `lore-le-marchand-borgne` | portrait, 1200×1700 | Personnage › PNJ | Le Marchand Borgne | A one-eyed merchant with an eyepatch behind a market stall cluttered with odd trinkets, sly smile |
| `lore-le-dragon-de-suie` | portrait, 1200×1700 | Personnage › Créature | Le Dragon de Suie | A dragon made of black smoke and soot, glowing embers for eyes, curling over a ruined fortress |
| `lore-lepee-sans-nom` | portrait, 1200×1700 | Objet | L'Épée sans Nom | An old sword engraved with faintly glowing runes, planted in a mossy stone, dramatic light |
| `lore-la-legende-du-lac-gris` | portrait, 1200×1700 | Lieu › Paysage | La Légende du Lac Gris | A perfectly still grey lake, the rooftops and spires of a sunken town visible under the water |

### La chronologie

| Fichier | Format | Dossier | Utilisée sur | Idée (prompt) |
|---|---|---|---|---|
| `evenement-la-nuit-des-cendres` | portrait, 1200×1700 | Événement | La Nuit des Cendres | A fortress burning at night, a smoke dragon above it, defenders silhouetted against the fire |
| `evenement-le-grand-brouillard` | portrait, 1200×1700 | Événement | Le Grand Brouillard | A towering wall of fog swallowing an entire valley, tiny villagers fleeing |
| `evenement-le-bal-des-lanternes` | portrait, 1200×1700 | Événement | Le Bal des Lanternes | Dancers on a cobbled town square at night, each holding a paper lantern, one lantern dancing on its own |
| `evenement-le-pacte-du-corbeau` | portrait, 1200×1700 | Événement | Le Pacte du Corbeau | Black-armoured knights kneeling to swear an oath before a large raven perched on a stone altar |

### Les gravures (illustrations dans le corps des fiches Lore)

| Fichier | Format | Dossier | Utilisée sur | Idée (prompt) |
|---|---|---|---|---|
| `gravure-erudit` | portrait, 1000×1400 | Site | articles des fiches Lore | Old woodcut engraving, black ink on cream paper: a scholar bent over a huge grimoire by candlelight |
| `gravure-bestiaire` | portrait, 1000×1400 | Site | articles des fiches Lore | Old woodcut engraving, black ink on cream paper: a bestiary page full of strange creatures and a small dragon |
