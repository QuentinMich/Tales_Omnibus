from django.test import TestCase
from django.urls import reverse

from campagnes.models import CampagnePage, CampagnesIndexPage, HeroPage
from encyclopedie.models import EncyclopedieIndexPage, LorePage
from home.models import HomePage


class RechercheTests(TestCase):
    """
    La recherche plein texte : elle trouve par le titre, le texte et les tags,
    met les titres en tête, et affiche des cartes en français.
    """

    def setUp(self):
        home = HomePage.objects.first()
        index = home.add_child(instance=CampagnesIndexPage(title="Campagnes"))
        self.campagne = index.add_child(instance=CampagnePage(title="Saison 1"))
        encyclopedie = home.add_child(instance=EncyclopedieIndexPage(title="Encyclopédie"))
        # Le dragon n'est nommé que dans le TEXTE de la Nuit, et en TAG des Cendres
        self.nuit = encyclopedie.add_child(instance=LorePage(
            title="La Nuit", intro="<p>Le dragon attaque le fort.</p>"))
        self.cendres = encyclopedie.add_child(instance=LorePage(title="Les Cendres"))
        self.cendres.tags.add("dragon")
        self.cendres.save_revision().publish()
        self.dragon = encyclopedie.add_child(instance=LorePage(
            title="Le Dragon de Suie", intro="<p>Il éternue des incendies.</p>"))

    def chercher(self, mot):
        return self.client.get(reverse("search"), {"query": mot})

    def titres(self, response):
        return [page.title for page in response.context["search_results"]]

    def test_trouve_par_le_titre_le_texte_et_les_tags(self):
        self.assertEqual(set(self.titres(self.chercher("dragon"))),
                         {"Le Dragon de Suie", "La Nuit", "Les Cendres"})

    def test_le_titre_passe_en_premier(self):
        self.assertEqual(self.titres(self.chercher("dragon"))[0], "Le Dragon de Suie")

    def test_resultats_en_cartes_avec_type_et_accroche(self):
        response = self.chercher("dragon")
        self.assertContains(response, "3 résultats pour « dragon »")
        self.assertContains(response, 'class="timeline-item fiche-typee"')
        self.assertContains(response, "Il éternue des incendies.")  # l'accroche, sans HTML

    def test_aucun_resultat(self):
        self.assertContains(self.chercher("licorne"), "Aucun résultat pour « licorne »")

    def test_la_page_de_resultats_n_est_pas_indexee_par_google(self):
        self.assertContains(self.chercher("dragon"), '<meta name="robots" content="noindex, follow" />')

    def test_le_champ_de_recherche_est_dans_le_header_de_chaque_page(self):
        hero = self.campagne.add_child(instance=HeroPage(title="Brann", joueur_nom="B"))
        for url in ("/", hero.url):
            self.assertContains(self.client.get(url), 'class="site-search"')

    def test_une_page_hors_limite_ne_plante_pas(self):
        response = self.client.get(reverse("search"), {"query": "dragon", "page": "999"})
        self.assertEqual(response.status_code, 200)
