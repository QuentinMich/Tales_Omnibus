from django.test import TestCase
from home.models import HomePage

from campagnes.models import CampagnePage, CampagnesIndexPage, CartePage, HeroPage, LieuPage
from encyclopedie.models import EncyclopedieIndexPage, LorePage, fiches_liees


class ArborescenceMixin:
    """
    Arborescence de test, partagée par les deux classes ci-dessous :
      Accueil > Encyclopédie > Lore « Les dieux »            (tag : Divin)
      Accueil > Campagnes > Saison 1 > Héros « Aldric »      (tag : Dragon)
                                     > Carte > Lieu « Port » (tag : dragon, en minuscule)
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
        carte = self.saison1.add_child(instance=CartePage(title="Carte"))
        port = carte.add_child(instance=LieuPage(title="Port"))
        port.tags.add("dragon")  # même tag grâce à TAGGIT_CASE_INSENSITIVE
        port.save()
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
        slugs = [slug for slug, nom in response.context['tags']]
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
