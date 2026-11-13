import os
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


class SlugAutomatiqueTests(TestCase):
    """Le client ne gère jamais les adresses : elles suivent le titre ou sont fixes."""

    def setUp(self):
        self.home = HomePage.objects.first()
        self.index = self.home.add_child(instance=CampagnesIndexPage(title="Tales", slug="tales"))
        self.campagne = self.index.add_child(instance=CampagnePage(title="Saison 1"))

    def test_page_unique_slug_fixe(self):
        # Peu importe le titre (ou le slug saisi), l'index s'appelle "campagnes"
        self.assertEqual(self.index.slug, "campagnes")

    def test_slug_suit_le_titre_sans_accent(self):
        self.campagne.title = "L'Éveil du Dragon"
        self.campagne.save_revision().publish()
        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.slug, "leveil-du-dragon")

    def test_renommer_cree_une_redirection(self):
        ancienne_url = self.campagne.url
        self.campagne.title = "Saison 2"
        # Wagtail crée la redirection "au commit" de la transaction ; un TestCase
        # ne commite jamais, donc on exécute ces callbacks à la main.
        with self.captureOnCommitCallbacks(execute=True):
            self.campagne.save_revision().publish()
        self.assertRedirects(self.client.get(ancienne_url), "/campagnes/saison-2/",
                             status_code=301)

    def test_deux_soeurs_meme_titre(self):
        jumelle = self.index.add_child(instance=CampagnePage(title="Saison 1"))
        self.assertEqual(jumelle.slug, "saison-1-2")

    def test_formulaire_admin_ignore_le_slug(self):
        # Le champ est en lecture seule : il n'est même pas dans le formulaire
        form_class = CampagnePage.get_edit_handler().get_form_class()
        self.assertNotIn("slug", form_class.base_fields)

    def test_commande_synchro_garde_les_adresses_des_enfants(self):
        # Simule une base d'avant le mixin : l'index s'appelle encore "tales"
        # (update() court-circuite save(), donc le mixin n'intervient pas)
        from django.core.management import call_command
        from wagtail.models import Page
        racine = self.home.url_path
        Page.objects.filter(id=self.index.id).update(slug="tales", url_path=f"{racine}tales/")
        Page.objects.filter(id=self.campagne.id).update(url_path=f"{racine}tales/saison-1/")

        call_command("synchroniser_slugs", stdout=open(os.devnull, "w"))

        # Bug corrigé : l'enfant ne doit pas être réenregistré avec l'ancienne adresse
        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.url_path, f"{racine}campagnes/saison-1/")
        self.assertEqual(self.client.get("/campagnes/saison-1/").status_code, 200)


class CreerDemoTests(TestCase):
    """La commande creer_demo crée une campagne complète et la retire proprement."""

    def setUp(self):
        from campagnes.models import CampagnesIndexPage
        from encyclopedie.models import EncyclopedieIndexPage
        from home.models import HomePage
        home = HomePage.objects.first()
        home.add_child(instance=CampagnesIndexPage(title="Campagnes"))
        home.add_child(instance=EncyclopedieIndexPage(title="Encyclopédie"))

    def test_creation_puis_suppression(self):
        from io import StringIO
        from django.core.management import call_command
        from wagtail.models import Page
        from campagnes.models import Apparition
        from encyclopedie.models import FamilleDeTags
        avant = Page.objects.count()

        call_command('creer_demo', stdout=StringIO())
        self.assertGreaterEqual(Page.objects.count() - avant, 20)
        self.assertEqual(Apparition.objects.count(), 8)
        # Les zones de la démo rangent les lieux : Hameau › Bois des Murmures › Ardenn
        hameau = Apparition.objects.get(lieu__title="Hameau des Saules")
        self.assertEqual([l.title for l in hameau.chemin()], ["Ardenn", "Bois des Murmures"])
        # Toutes les pages de la démo s'affichent
        for page in Page.objects.live().specific().filter(depth__gt=2):
            self.assertEqual(self.client.get(page.url).status_code, 200, page.title)

        call_command('creer_demo', '--supprimer', stdout=StringIO())
        self.assertEqual(Page.objects.count(), avant)
        self.assertFalse(FamilleDeTags.objects.exists())

        call_command('creer_demo', stdout=StringIO())  # et on peut la recréer


class SeoAutomatiqueTests(TestCase):
    """core/seo.py : titre et méta description générés quand l'admin les laisse vides."""

    def setUp(self):
        from encyclopedie.models import EncyclopedieIndexPage, LorePage
        from core.models import Categorie
        from home.models import HomePage
        self.home = HomePage.objects.first()
        encyclopedie = self.home.add_child(instance=EncyclopedieIndexPage(title="Encyclopédie"))
        self.deite = Categorie.objects.create(nom="Déité majeure")
        self.vael = encyclopedie.add_child(instance=LorePage(
            title="Vaël", categorie=self.deite,
            intro="<p>Elle tisse le <b>brouillard</b>&nbsp;et décide qui s'y perd.</p>",
        ))
        self.vael.save_revision().publish()

    def test_couper_a_la_fin_d_un_mot(self):
        from core.seo import couper
        texte = "mot " * 60
        coupe = couper(texte.strip())
        self.assertLessEqual(len(coupe), 155)
        self.assertTrue(coupe.endswith("mot…"))

    def test_titre_et_description_automatiques(self):
        from core.seo import description_seo, titre_seo
        self.assertEqual(titre_seo(self.vael, "Tales Omnibus"), "Vaël · Déité majeure | Tales Omnibus")
        # HTML retiré, entités (&nbsp;) décodées, espaces normalisés
        self.assertEqual(description_seo(self.vael, "Tales Omnibus"), "Elle tisse le brouillard et décide qui s'y perd.")

    def test_les_champs_promotion_du_client_ont_la_priorite(self):
        from core.seo import description_seo, titre_seo
        self.vael.seo_title = "La déesse des Brumes"
        self.vael.search_description = "Tout sur Vaël."
        self.assertEqual(titre_seo(self.vael, "Tales Omnibus"), "La déesse des Brumes | Tales Omnibus")
        self.assertEqual(description_seo(self.vael, "Tales Omnibus"), "Tout sur Vaël.")

    def test_le_head_de_la_page(self):
        html = self.client.get(self.vael.url).content.decode()
        self.assertIn("<title>Vaël · Déité majeure | Tales Omnibus</title>", html)
        self.assertIn('<meta name="description" content="Elle tisse le brouillard et décide qui s&#x27;y perd." />', html)
        self.assertIn('<meta property="og:type" content="article" />', html)
        self.assertIn('<link rel="canonical" href="http://localhost/encyclopedie/vael/" />', html)

    def test_l_accueil_porte_le_nom_du_site(self):
        self.assertContains(self.client.get(self.home.url), "<title>Tales Omnibus</title>", html=False)
