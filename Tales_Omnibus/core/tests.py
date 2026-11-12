from django.test import RequestFactory, TestCase
from wagtail.blocks.struct_block import StructBlockValidationError

from campagnes.models import CampagnePage, CampagnesIndexPage
from core.blocks import StreamPlayerBlock
from home.models import HomePage


class MenuPrincipalTests(TestCase):
    """Le menu garde ses mots fixes, quels que soient les titres des pages."""

    def setUp(self):
        self.home = HomePage.objects.first()
        # Titre "fantaisie" exprès : le menu doit quand même dire "Campagnes"
        self.index = self.home.add_child(instance=CampagnesIndexPage(title="Tales"))
        self.campagne = self.index.add_child(instance=CampagnePage(title="Saison 1"))

    def test_libelle_fixe_et_pas_le_titre(self):
        response = self.client.get(self.home.url)
        self.assertContains(response, "Campagnes")
        self.assertNotContains(response, ">Tales<")

    def test_rubrique_active_sur_une_sous_page(self):
        # Sur une campagne, c'est l'entrée "Campagnes" qui est active, pas "Accueil"
        items = self.client.get(self.campagne.url).context['items']
        actifs = [item['libelle'] for item in items if item['actif']]
        self.assertEqual(actifs, ["Campagnes"])

    def test_page_absente_pas_de_lien(self):
        # Ni Univers, ni Encyclopédie, ni Contact n'existent dans ce test
        libelles = [item['libelle'] for item in self.client.get(self.home.url).context['items']]
        self.assertEqual(libelles, ["Accueil", "Campagnes"])

    def test_retour_libelle_fixe_vers_une_rubrique(self):
        # Le parent s'appelle "Tales" dans l'admin, mais le lien dit "aux campagnes"
        self.assertContains(self.client.get(self.campagne.url), "Retour aux campagnes")

    def test_pas_de_retour_sur_l_accueil(self):
        self.assertNotContains(self.client.get(self.home.url), "btn-back")


class StreamPlayerBlockTests(TestCase):
    def setUp(self):
        self.block = StreamPlayerBlock()

    def valeur(self, plateforme, chaine):
        return self.block.to_python({'plateforme': plateforme, 'chaine': chaine, 'titre': ''})

    def test_twitch_avec_le_domaine_du_site(self):
        request = RequestFactory().get('/', HTTP_HOST='monsite.fr:8000')
        html = self.block.render(self.valeur('twitch', 'machaine'), context={'request': request})
        self.assertIn('channel=machaine', html)
        self.assertIn('parent=monsite.fr', html)  # sans le port

    def test_youtube_refuse_un_pseudo(self):
        with self.assertRaises(StructBlockValidationError):
            self.block.clean(self.valeur('youtube', '@MaChaine'))

    def test_youtube_accepte_un_id_de_chaine(self):
        valeur = self.block.clean(self.valeur('youtube', 'UC' + 'a' * 22))
        self.assertIn('live_stream?channel=UC', self.block.render(valeur))
