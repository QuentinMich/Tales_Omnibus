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
        self.assertEqual(Apparition.objects.count(), 9)
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


class AltAutomatiqueTests(TestCase):
    """L'ALT construit à partir des dossiers (collections), du titre et de la description."""

    def setUp(self):
        from wagtail.images import get_image_model
        from wagtail.images.tests.utils import get_test_image_file
        from wagtail.models import Collection
        racine = Collection.get_first_root_node()
        personnage = racine.add_child(name="Personnage")
        self.heros = personnage.add_child(name="Héros")
        self.Image = get_image_model()
        self.fichier = get_test_image_file

    def image(self, titre, collection=None, description=""):
        from wagtail.models import Collection
        return self.Image.objects.create(title=titre, file=self.fichier(), description=description,
                                         collection=collection or Collection.get_first_root_node())

    def test_dossiers_et_titre(self):
        from core.images import texte_alternatif
        image = self.image("Brann_le_Rouquin", self.heros)
        self.assertEqual(texte_alternatif(image), "Personnage, Héros : Brann le Rouquin")

    def test_la_description_s_ajoute(self):
        from core.images import texte_alternatif
        image = self.image("Brann", self.heros, "Une hache sur l'épaule.")
        self.assertEqual(texte_alternatif(image), "Personnage, Héros : Brann. Une hache sur l'épaule.")

    def test_sans_dossier_le_titre_seul(self):
        from core.images import texte_alternatif
        # Les tirets restent : ce sont souvent des noms propres
        self.assertEqual(texte_alternatif(self.image("Port-Lanterne")), "Port-Lanterne")


class DossiersEtDocumentsTests(TestCase):
    """Le squelette de dossiers (migration core 0005) et le bloc « Document »."""

    def test_le_squelette_de_dossiers_existe(self):
        from wagtail.models import Collection
        personnage = Collection.objects.get(name="Personnage", depth=2)
        self.assertEqual(sorted(c.name for c in personnage.get_children()), ["Créature", "Déité", "Héros", "PNJ"])
        self.assertTrue(Collection.objects.filter(name="Aide de jeu", depth=2).exists())

    def test_relancer_la_migration_ne_cree_pas_de_doublon(self):
        import importlib
        from wagtail.models import Collection
        migration = importlib.import_module("core.migrations.0005_dossiers_de_medias")
        avant = Collection.objects.count()
        migration.creer_les_dossiers(None, None)
        self.assertEqual(Collection.objects.count(), avant)

    def test_le_bloc_document(self):
        from django.core.files.base import ContentFile
        from wagtail.documents import get_document_model
        from core.blocks import DocumentBlock
        document = get_document_model()(title="Lettre")
        document.file.save("lettre.pdf", ContentFile(b"x" * 2048), save=False)
        document.save()
        bloc = DocumentBlock()
        html = bloc.render(bloc.to_python({'document': document.pk, 'titre': "", 'description': "Trouvée sur la route."}))
        self.assertIn("Lettre", html)                 # titre vide : celui du document
        self.assertIn("Trouvée sur la route.", html)
        self.assertIn(f'href="{document.url}"', html)
        self.assertIn("(PDF, 2,0", html)              # type + poids, à la française
        document.file.delete(save=False)


class EntretienTests(TestCase):
    """manage.py entretien et la page « Entretien du site » de l'admin."""

    def setUp(self):
        from campagnes.models import CampagnePage, CampagnesIndexPage
        from home.models import HomePage
        self.home = HomePage.objects.first()
        index = self.home.add_child(instance=CampagnesIndexPage(title="Campagnes"))
        self.campagne = index.add_child(instance=CampagnePage(title="Saison 1"))

    def lancer(self, **options):
        from core.entretien import lancer_entretien
        options.setdefault('sauvegarder', False)  # pas de copie de base pendant les tests
        options.setdefault('migrer', False)
        return {etape.titre: etape.lignes for etape in lancer_entretien(**options)}

    def test_supprime_une_redirection_devenue_inutile(self):
        from wagtail.contrib.redirects.models import Redirect
        # La page est revenue à son ancienne adresse : la redirection la masquerait
        Redirect.objects.create(old_path=self.campagne.url, redirect_page=self.home)
        self.lancer()
        self.assertFalse(Redirect.objects.filter(old_path=Redirect.normalise_path(self.campagne.url)).exists())

    def test_raccourcit_une_chaine_de_redirections(self):
        from wagtail.contrib.redirects.models import Redirect
        Redirect.objects.create(old_path="/a", redirect_link="/b")
        Redirect.objects.create(old_path="/b", redirect_page=self.campagne)
        self.lancer()
        self.assertEqual(Redirect.objects.get(old_path="/a").redirect_page, self.campagne.page_ptr)

    def test_la_simulation_ne_change_rien(self):
        from wagtail.contrib.redirects.models import Redirect
        Redirect.objects.create(old_path=self.campagne.url, redirect_page=self.home)
        compte_rendu = self.lancer(simulation=True)
        self.assertEqual(Redirect.objects.count(), 1)
        self.assertTrue(any("Inutile" in ligne for ligne in compte_rendu["Redirections"]))

    def test_tout_publier(self):
        from campagnes.models import CampagnePage
        brouillon = self.campagne.get_parent().add_child(instance=CampagnePage(title="Saison 2", live=False))
        brouillon.save_revision()
        self.lancer(publier=True)
        self.assertTrue(CampagnePage.objects.get(pk=brouillon.pk).live)

    def test_sans_l_option_rien_n_est_publie(self):
        from campagnes.models import CampagnePage
        brouillon = self.campagne.get_parent().add_child(instance=CampagnePage(title="Saison 2", live=False))
        brouillon.save_revision()
        compte_rendu = self.lancer()
        self.assertFalse(CampagnePage.objects.get(pk=brouillon.pk).live)
        self.assertTrue(any("Saison 2" in ligne for ligne in compte_rendu["À vérifier"]))

    def test_la_commande_tourne(self):
        from io import StringIO
        from django.core.management import call_command
        sortie = StringIO()
        call_command("entretien", "--simulation", "--sans-sauvegarde", stdout=sortie)
        self.assertIn("Simulation terminée", sortie.getvalue())

    def test_la_page_d_admin_est_reservee_aux_administrateurs(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        from django.urls import reverse
        Utilisateur = get_user_model()
        url = reverse("entretien_du_site")
        editeur = Utilisateur.objects.create_user("editeur", "e@example.com", "x")
        editeur.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.client.force_login(editeur)
        # Wagtail transforme le refus (PermissionDenied) en retour au tableau
        # de bord avec un message : une redirection, pas la page
        refus = self.client.get(url)
        self.assertEqual(refus.status_code, 302)
        self.assertNotContains(refus, "Lancer l'entretien", status_code=302)

        self.client.force_login(Utilisateur.objects.create_superuser("admin", "a@example.com", "x"))
        page = self.client.get(url)
        self.assertContains(page, "Lancer l'entretien")
        resultat = self.client.post(url, {"action": "simulation"})
        self.assertContains(resultat, "Vérification (rien n&#x27;a été modifié)")
        self.assertContains(resultat, "Géographie des cartes")


class MenuAdminTests(TestCase):
    """Le menu de gauche de l'admin, réorganisé pour un non-codeur."""

    def menu_pour(self, utilisateur):
        from django.test import RequestFactory
        from wagtail.admin.menu import admin_menu
        requete = RequestFactory().get("/admin/")
        requete.user = utilisateur
        entrees = sorted(admin_menu.menu_items_for_request(requete), key=lambda e: e.order)
        return [
            (e.label, [s.label for s in sorted(e.menu.menu_items_for_request(requete), key=lambda s: s.order)]
             if hasattr(e, "menu") else None)
            for e in entrees
        ]

    def test_le_menu_d_un_administrateur(self):
        from django.contrib.auth import get_user_model
        from home.models import HomePage
        from pages.models import ContactPage
        # « Messages » n'apparaît que s'il existe un formulaire (la page Contact)
        HomePage.objects.first().add_child(instance=ContactPage(title="Contact"))
        admin = get_user_model().objects.create_superuser("admin", "a@example.com", "x")
        menu = dict(self.menu_pour(admin))
        self.assertEqual(list(menu)[:3], ["Plan du site", "Univers", "Dossiers"])
        self.assertEqual(menu["Organisation"], ["Catégories", "Familles de tags", "Prestations"])
        self.assertEqual(menu["Comptes"], ["Utilisateurs", "Groupes"])
        self.assertEqual(menu["Paramètres avancés"], ["Sites", "Redirections", "Workflows", "Tâches de workflow"])
        for libelle in ("Images", "Documents", "Messages", "Paramètres du site", "Entretien du site", "Rapports"):
            self.assertIn(libelle, menu)
        # Les anciens noms techniques ont disparu
        for ancien in ("Pages", "Fragments", "Formulaires", "Paramètres"):
            self.assertNotIn(ancien, menu)


class EntretienMigrationsEnAttenteTests(TestCase):
    """Juste après un pull : la simulation et le bouton de l'admin ne doivent pas planter."""

    def test_s_arrete_proprement_si_des_migrations_attendent(self):
        from unittest.mock import patch
        from core.entretien import lancer_entretien
        # On fait croire qu'une migration vient d'arriver par un pull
        with patch("core.entretien.migrations_en_attente", return_value=["campagnes 9999_nouvelle"]):
            for options in ({"simulation": True, "migrer": True}, {"migrer": False}):
                titres = [e.titre for e in lancer_entretien(sauvegarder=False, **options)]
                self.assertEqual(titres[-1], "Arrêt")
                self.assertNotIn("Redirections", titres)  # la suite n'a pas été lancée
