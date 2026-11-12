from django.test import TestCase
from home.models import HomePage

from campagnes.models import CampagnePage, CampagnesIndexPage, CartePage, HeroPage, LieuPage
from encyclopedie.models import EncyclopedieIndexPage, LorePage


class EncyclopedieTests(TestCase):
    """
    Arborescence de test :
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
