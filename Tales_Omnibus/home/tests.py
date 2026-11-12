from home.models import HomePage

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        root_page = Page.get_first_root_node()
        Site.objects.create(hostname="testsite", root_page=root_page, is_default_site=True)
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "home/home_page.html")


class HomeContenuTests(WagtailPageTestCase):
    """L'accueil du wireframe : image d'ouverture, campagnes, univers."""

    def setUp(self):
        from campagnes.models import CampagnePage, CampagnesIndexPage
        from pages.models import StandardPage

        # L'accueil créé par les migrations, déjà relié au site par défaut
        self.home = HomePage.objects.first()
        index = self.home.add_child(instance=CampagnesIndexPage(title="Campagnes"))
        for i in range(4):
            index.add_child(instance=CampagnePage(title=f"Campagne {i}"))
        self.univers = self.home.add_child(instance=StandardPage(
            title="Mon univers", intro="Intro de la page univers"))

    def get_home(self):
        return self.client.get(self.home.url)

    def test_trois_campagnes_maximum(self):
        # 4 campagnes publiées, mais le wireframe n'en montre que 3
        self.assertEqual(len(self.get_home().context['campagnes']), 3)

    def test_image_avant_le_header(self):
        html = self.get_home().content.decode()
        self.assertLess(html.index('home-hero'), html.index('site-header'))

    def test_univers_reprend_l_intro_si_pas_d_accroche(self):
        self.home.page_univers = self.univers
        self.home.save_revision().publish()
        self.assertContains(self.get_home(), "Intro de la page univers")

    def test_univers_accroche_personnalisee(self):
        self.home.page_univers = self.univers
        self.home.univers_accroche = "Une accroche sur mesure"
        self.home.save_revision().publish()
        response = self.get_home()
        self.assertContains(response, "Une accroche sur mesure")
        self.assertNotContains(response, "Intro de la page univers")
