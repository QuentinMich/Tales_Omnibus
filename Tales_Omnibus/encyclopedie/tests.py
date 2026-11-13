from django.test import TestCase
from home.models import HomePage

from campagnes.models import Apparition, CampagnePage, CampagnesIndexPage, CartePage, HeroPage, LieuPage
from encyclopedie.models import EncyclopedieIndexPage, LorePage, fiches_liees


class ArborescenceMixin:
    """
    Arborescence de test, partagée par les deux classes ci-dessous :
      Accueil > Encyclopédie > Lore « Les dieux »            (tag : Divin)
      Accueil > Campagnes > Saison 1 > Héros « Aldric »      (tag : Dragon)
                                     > Carte (où apparaît le Lieu « Port », rangé
                                              dans l'encyclopédie, tag : dragon en minuscule)
                          > Saison 2 > Héros « Brune »       (sans tag)
    """

    def setUp(self):
        home = HomePage.objects.first()
        self.encyclopedie = home.add_child(instance=EncyclopedieIndexPage(title="Encyclopédie"))
        lore = self.encyclopedie.add_child(instance=LorePage(title="Les dieux"))
        lore.tags.add("Divin")
        lore.save()

        index = home.add_child(instance=CampagnesIndexPage(title="Campagnes"))
        self.saison1 = index.add_child(instance=CampagnePage(title="Saison 1"))
        saison2 = index.add_child(instance=CampagnePage(title="Saison 2"))

        self.aldric = self.saison1.add_child(instance=HeroPage(title="Aldric", joueur_nom="Bob"))
        self.aldric.tags.add("Dragon")
        self.aldric.save()
        # Les lieux vivent dans l'encyclopédie et sont POSÉS sur des cartes
        port = self.encyclopedie.add_child(instance=LieuPage(title="Port"))
        port.tags.add("dragon")  # même tag grâce à TAGGIT_CASE_INSENSITIVE
        port.save()
        carte = self.saison1.add_child(instance=CartePage(title="Carte"))
        Apparition.objects.create(carte=carte, lieu=port, coord_x=50, coord_y=50)
        saison2.add_child(instance=HeroPage(title="Brune", joueur_nom="Zoé"))


class EncyclopedieTests(ArborescenceMixin, TestCase):
    def titres(self, **filtres):
        response = self.client.get(self.encyclopedie.url, filtres)
        return [fiche.title for fiche in response.context['fiches']]

    def test_sans_filtre_toutes_les_fiches(self):
        self.assertEqual(self.titres(), ["Aldric", "Brune", "Les dieux", "Port"])

    def test_filtre_par_campagne_ecarte_le_lore(self):
        self.assertEqual(self.titres(campagne=self.saison1.pk), ["Aldric", "Port"])

    def test_filtre_par_type(self):
        self.assertEqual(self.titres(type="heros"), ["Aldric", "Brune"])

    def test_filtre_par_tag_insensible_a_la_casse(self):
        self.assertEqual(self.titres(tag="dragon"), ["Aldric", "Port"])

    def test_filtres_combines(self):
        self.assertEqual(self.titres(type="lieux", tag="dragon"), ["Port"])

    def test_valeurs_inconnues_ignorees(self):
        # Une URL bricolée ne doit pas faire planter la page
        response = self.client.get(self.encyclopedie.url, {'campagne': "abc", 'type': "pirate"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['fiches']), 4)

    def test_les_tags_restent_proposes_apres_un_choix(self):
        response = self.client.get(self.encyclopedie.url, {'tag': "dragon"})
        slugs = [tag.slug for groupe in response.context['groupes_de_tags'] for tag in groupe['tags']]
        self.assertEqual(slugs, ["divin", "dragon"])

    def test_le_tag_d_une_fiche_mene_a_l_encyclopedie_filtree(self):
        response = self.client.get(self.aldric.url)
        self.assertContains(response, f'href="{self.encyclopedie.url}?tag=dragon"')

    # --- Épingler ---------------------------------------------------------
    def test_les_fiches_epinglees_passent_en_premier(self):
        port = LieuPage.objects.get(title="Port")
        port.epinglee = True
        port.save_revision().publish()
        self.assertEqual(self.titres(), ["Port", "Aldric", "Brune", "Les dieux"])

    # --- Couleur par type -------------------------------------------------
    def test_chaque_carte_porte_son_type(self):
        response = self.client.get(self.encyclopedie.url)
        self.assertContains(response, 'data-type="heros"')
        self.assertContains(response, 'data-type="lore"')

    # --- Pagination -------------------------------------------------------
    def test_pagination_garde_les_filtres(self):
        EncyclopedieIndexPage.FICHES_PAR_PAGE = 1  # 1 fiche par page pour le test
        self.addCleanup(setattr, EncyclopedieIndexPage, 'FICHES_PAR_PAGE', 12)
        response = self.client.get(self.encyclopedie.url, {'tag': "dragon"})
        self.assertEqual([f.title for f in response.context['fiches']], ["Aldric"])
        # Le lien "Suivantes" garde le tag dans l'URL
        self.assertContains(response, '?tag=dragon&amp;page=2')
        self.assertEqual(self.titres(tag="dragon", page=2), ["Port"])

    def test_numero_de_page_invalide(self):
        self.assertEqual(len(self.titres(page="abc")), 4)


    # --- Arbre des catégories -----------------------------------------------
    def creer_arbre(self):
        """
        Personnage (défaut des héros)          Divers (défaut du lore)
        ├─ PNJ                                 Lieu (défaut des lieux)
        └─ Déité                               └─ Port de commerce
           └─ Déité mineure
        """
        from core.models import Categorie
        C = Categorie.objects.create
        self.personnage = C(nom="Personnage", par_defaut_pour='heros', couleur="#A23B3B")
        self.pnj = C(nom="PNJ", parent=self.personnage)
        self.deite = C(nom="Déité", parent=self.personnage)
        self.mineure = C(nom="Déité mineure", parent=self.deite)
        self.divers = C(nom="Divers", par_defaut_pour='lore')
        self.lieu = Categorie.objects.get(par_defaut_pour="lieux")  # créée par la migration core 0004
        self.port_cat = C(nom="Port de commerce", parent=self.lieu)

    def test_une_categorie_inclut_toute_sa_branche(self):
        self.creer_arbre()
        dieux = LorePage.objects.get(title="Les dieux")
        dieux.categorie = self.mineure  # une fiche Lore… rangée dans Personnage !
        dieux.save_revision().publish()
        # Personnage = les héros (par défaut, sans catégorie) + la déité mineure
        self.assertEqual(self.titres(categorie=self.personnage.pk), ["Aldric", "Brune", "Les dieux"])
        self.assertEqual(self.titres(categorie=self.deite.pk), ["Les dieux"])

    def test_categorie_par_defaut_du_type(self):
        self.creer_arbre()
        # « Les dieux » n'a pas de catégorie : c'est une fiche Lore -> « Divers »
        self.assertEqual(self.titres(categorie=self.divers.pk), ["Les dieux"])
        response = self.client.get(self.encyclopedie.url)
        self.assertContains(response, '<span class="fiche-type">Divers</span>', html=True)

    def test_le_menu_montre_l_arbre_indente(self):
        self.creer_arbre()
        options = dict(self.client.get(self.encyclopedie.url).context['options_categories'])
        self.assertEqual(options[self.mineure.pk], "\u00a0" * 6 + "Déité mineure")  # profondeur 2
        self.assertEqual(options[self.personnage.pk], "Personnage")

    def test_couleur_heritee_du_parent(self):
        self.creer_arbre()
        self.assertEqual(self.mineure.couleur_effective, "#A23B3B")
        self.assertEqual(str(self.mineure), "Personnage › Déité › Déité mineure")

    def test_pas_de_boucle_dans_l_arbre(self):
        from core.models import Categorie, CategorieForm
        self.creer_arbre()
        Form = type('F', (CategorieForm,), {'Meta': type('Meta', (), {
            'model': Categorie, 'fields': ['nom', 'parent', 'ordre']})})
        # « Personnage » rangé dans sa propre petite-fille : refusé
        form = Form(instance=self.personnage, data={'nom': "Personnage", 'parent': self.mineure.pk, 'ordre': 0})
        self.assertFalse(form.is_valid())

    def test_badge_sur_la_fiche(self):
        self.creer_arbre()
        self.assertContains(self.client.get(self.aldric.url), "Personnage")

    def test_chaque_niveau_du_badge_mene_a_l_encyclopedie_filtree(self):
        self.creer_arbre()
        dieux = LorePage.objects.get(title="Les dieux")
        dieux.categorie = self.mineure
        dieux.save_revision().publish()
        html = self.client.get(dieux.url).content.decode()
        for categorie in (self.personnage, self.deite, self.mineure):
            self.assertIn(f'href="{self.encyclopedie.url}?categorie={categorie.pk}"', html)


class FichesLieesTests(ArborescenceMixin, TestCase):
    def test_fiches_liees_par_tag_commun(self):
        self.assertEqual([f.title for f in fiches_liees(self.aldric)], ["Port"])

    def test_la_plus_proche_d_abord(self):
        # "Les dieux" partage 2 tags avec Aldric, "Port" un seul
        lore = LorePage.objects.get(title="Les dieux")
        lore.tags.add("Dragon")
        lore.save()
        self.aldric.tags.add("Divin")
        self.aldric.save()
        self.assertEqual([f.title for f in fiches_liees(self.aldric)], ["Les dieux", "Port"])

    def test_encart_affiche_sur_la_fiche(self):
        response = self.client.get(self.aldric.url)
        self.assertContains(response, "Fiches liées")
        self.assertContains(response, "Port")

    def test_pas_de_tag_pas_d_encart(self):
        brune = HeroPage.objects.get(title="Brune")
        self.assertNotContains(self.client.get(brune.url), "Fiches liées")



class FamillesDeTagsTests(ArborescenceMixin, TestCase):
    """Le snippet range les tags existants : « dragon » dans « Créatures »."""

    def setUp(self):
        super().setUp()
        from taggit.models import Tag
        from encyclopedie.models import FamilleDeTags
        self.Tag, self.Famille = Tag, FamilleDeTags
        self.creatures = FamilleDeTags.objects.create(nom="Créatures", couleur="#A23B3B", ordre=1)
        self.creatures.tags.add(Tag.objects.get(slug="dragon"))

    def test_les_filtres_sont_groupes_par_famille(self):
        groupes = self.client.get(self.encyclopedie.url).context['groupes_de_tags']
        resume = [(g['famille'].nom if g['famille'] else None, [t.slug for t in g['tags']]) for g in groupes]
        # La famille d'abord, les tags sans famille dans « Autres » à la fin
        self.assertEqual(resume, [("Créatures", ["dragon"]), (None, ["divin"])])

    def test_ordre_des_familles(self):
        divins = self.Famille.objects.create(nom="Divin", ordre=0)  # ordre 0 : avant Créatures
        divins.tags.add(self.Tag.objects.get(slug="divin"))
        groupes = self.client.get(self.encyclopedie.url).context['groupes_de_tags']
        self.assertEqual([g['famille'].nom for g in groupes], ["Divin", "Créatures"])

    def test_la_fiche_affiche_la_couleur_de_la_famille(self):
        response = self.client.get(self.aldric.url)
        self.assertContains(response, 'title="Créatures"')
        self.assertContains(response, "--tag-color: #A23B3B")

    def test_un_tag_dans_une_seule_famille(self):
        from encyclopedie.models import FamilleDeTagsForm
        autre = self.Famille(nom="Monstres")
        FormClass = type('F', (FamilleDeTagsForm,), {'Meta': type('Meta', (), {
            'model': self.Famille, 'fields': ['nom', 'couleur', 'ordre', 'tags']})})
        form = FormClass(instance=autre, data={
            'nom': "Monstres", 'couleur': "#000000", 'ordre': 2,
            'tags': [self.Tag.objects.get(slug="dragon").pk],
        })
        self.assertFalse(form.is_valid())
        self.assertIn("Déjà rangé dans une autre famille : Dragon", str(form.errors))


class CampagnesDesFichesTests(ArborescenceMixin, TestCase):
    """Dans quelles campagnes est une fiche ? (campagnes_de + PresenceEnCampagne)"""

    def setUp(self):
        super().setUp()
        from encyclopedie.models import PresenceEnCampagne
        self.dieux = LorePage.objects.get(title="Les dieux")
        PresenceEnCampagne.objects.create(fiche=self.dieux, campagne=self.saison1,
                                          texte="Vénérés en secret.")

    def test_campagnes_de_chaque_type(self):
        from encyclopedie.models import campagnes_de
        port = LieuPage.objects.get(title="Port")
        for fiche in (self.aldric, port, self.dieux):  # héros, lieu, lore
            self.assertEqual([c.title for c, _ in campagnes_de(fiche)], ["Saison 1"], fiche.title)

    def test_le_lore_present_apparait_dans_le_filtre_de_campagne(self):
        response = self.client.get(self.encyclopedie.url, {'campagne': self.saison1.pk})
        self.assertIn("Les dieux", [f.title for f in response.context['fiches']])

    def test_section_dans_les_campagnes(self):
        response = self.client.get(self.dieux.url)
        self.assertContains(response, "Dans les campagnes")
        self.assertContains(response, "Vénérés en secret.")
        # Un héros n'a pas cette section : sa campagne est déjà sa page parente
        self.assertNotContains(self.client.get(self.aldric.url), "Dans les campagnes")


class StructureDesFichesTests(ArborescenceMixin, TestCase):
    """Le squelette commun : un seul h1, <article>, <aside>, et les blocs d'article."""

    def test_structure_semantique(self):
        html = self.client.get(self.aldric.url).content.decode()
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn('<article class="fiche">', html)
        self.assertIn('<aside class="fiche-annexes"', html)
        self.assertIn('<nav aria-label="Mots-clés">', html)

    def test_blocs_section_image_separateur(self):
        from wagtail.images.tests.utils import get_test_image_file
        from wagtail.images.models import Image
        image = Image.objects.create(title="test", file=get_test_image_file())
        dieux = LorePage.objects.get(title="Les dieux")
        dieux.body = [
            ('section', {'titre': "Origines", 'texte': "<p>Au commencement…</p>"}),
            ('image', {'image': image, 'caption': "", 'alt_text': "", 'position': 'droite'}),
            ('separateur', None),
        ]
        dieux.save_revision().publish()
        html = self.client.get(dieux.url).content.decode()
        self.assertIn('<section class="article-section">', html)
        self.assertIn('<h2 class="article-section-titre">Origines</h2>', html)
        self.assertIn('block-image--droite', html)
        self.assertIn('<hr class="separateur">', html)
