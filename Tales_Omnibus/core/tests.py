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

    def test_un_chemin_en_retard_sur_le_slug_est_repare(self):
        # Le bug de « Caer-Fiodh » : slug à jour, url_path resté ancien (page
        # déplacée puis renommée). Les liens menaient alors à une 404.
        from io import StringIO
        from django.core.management import call_command
        from wagtail.contrib.redirects.models import Redirect
        from wagtail.models import Page
        self.campagne.save_revision().publish()
        Page.objects.filter(pk=self.campagne.pk).update(url_path="/home/campagnes/ancien-nom/")
        self.campagne.refresh_from_db()
        self.assertEqual(self.client.get(self.campagne.url).status_code, 404)

        sortie = StringIO()
        call_command("synchroniser_slugs", stdout=sortie)
        self.assertIn("adresse réparée", sortie.getvalue())
        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.url_path, "/home/campagnes/saison-1/")
        self.assertEqual(self.client.get(self.campagne.url).status_code, 200)
        # L'ancienne adresse redirige (301) vers la page
        self.assertTrue(Redirect.objects.filter(old_path="/campagnes/ancien-nom", redirect_page=self.campagne).exists())

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
        # 7 lieux sur la carte d'Ardenn + le Val Gris et sa forteresse sur la carte détaillée
        self.assertEqual(Apparition.objects.count(), 9)
        # Les zones de la démo rangent les lieux : Hameau › Bois des Murmures › Ardenn
        hameau = Apparition.objects.get(lieu__title="Hameau des Saules")
        self.assertEqual([l.title for l in hameau.chemin()], ["Ardenn", "Bois des Murmures"])
        # Carte reliée : la carte du Val Gris détaille le royaume, posé sur Ardenn
        from campagnes.models import CartePage, ids_situes_dans
        val_gris = CartePage.objects.get(title="Carte du Val Gris")
        self.assertEqual([c.title for c in val_gris.cartes_englobantes()], ["Carte d'Ardenn"])
        # Le Val Gris entoure la forteresse, présente sur les deux cartes ;
        # le port, sur la côte, reste dans Ardenn
        fort = Apparition.objects.get(carte__title="Carte d'Ardenn", lieu__title="Fort-Sombre")
        self.assertEqual([l.title for l in fort.chemin()], ["Ardenn", "Royaume du Val Gris"])
        port = Apparition.objects.get(carte__title="Carte d'Ardenn", lieu__title="Port-Lanterne")
        self.assertEqual([l.title for l in port.chemin()], ["Ardenn"])
        # Le filtre géographique « tout ce qui est dans le Val Gris » : le fort, pas le port
        dans_le_val_gris = ids_situes_dans(val_gris.lieu_detaille_id)
        self.assertIn(fort.lieu_id, dans_le_val_gris)
        self.assertNotIn(port.lieu_id, dans_le_val_gris)
        # Toutes les pages de la démo s'affichent, avec UN seul <h1> (SEO),
        # et aucune image sans attribut alt (vide = décorative, mais présent)
        import re
        for page in Page.objects.live().specific().filter(depth__gt=1):
            reponse = self.client.get(page.url)
            self.assertEqual(reponse.status_code, 200, page.title)
            html = reponse.content.decode()
            self.assertEqual(html.count("<h1"), 1, page.title)
            self.assertFalse([img for img in re.findall(r"<img\b[^>]*>", html) if " alt=" not in img], page.title)

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
        # « Bien démarrer » en tête : la première chose à faire sur un site neuf
        self.assertEqual(list(menu)[:4], ["Bien démarrer", "Plan du site", "Univers", "Dossiers"])
        self.assertEqual(menu["Organisation"], ["Catégories", "Familles de tags", "Prestations"])
        self.assertEqual(menu["Comptes"], ["Utilisateurs", "Groupes"])
        self.assertEqual(menu["Paramètres avancés"], ["Sites", "Redirections", "Workflows", "Tâches de workflow"])
        for libelle in ("Images", "Documents", "Messages", "Paramètres du site", "Entretien du site", "Rapports"):
            self.assertIn(libelle, menu)
        # Les anciens noms techniques ont disparu
        for ancien in ("Pages", "Fragments", "Formulaires", "Paramètres"):
            self.assertNotIn(ancien, menu)

    def test_bien_demarrer_cache_aux_redacteurs(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        redacteur = get_user_model().objects.create_user("redac", "r@example.com", "x")
        redacteur.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.assertNotIn("Bien démarrer", dict(self.menu_pour(redacteur)))


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


class LogoEtSvgTests(TestCase):
    """Le logo garde sa forme, et un SVG de la médiathèque ne peut pas exécuter de script."""

    SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="60" viewBox="0 0 300 60">'
           b'<rect width="300" height="60" fill="#C9A24A"/></svg>')

    def setUp(self):
        from django.core.files.base import ContentFile
        from wagtail.images.models import Image
        from core.models import NavigationSettings
        self.logo = Image.objects.create(title="Logo en bannière", file=ContentFile(self.SVG, name="logo.svg"))
        reglages = NavigationSettings.load()
        reglages.logo = self.logo
        reglages.save()

    def test_le_logo_svg_reste_un_svg_et_n_est_pas_recadre(self):
        response = self.client.get(HomePage.objects.first().url)
        rendition = self.logo.get_rendition("max-320x96")
        self.assertTrue(rendition.url.endswith(".svg"))
        self.assertContains(response, rendition.url)
        # Bannière 300x60 réduite à 96 de haut maximum : les proportions sont gardées
        self.assertEqual((rendition.width, rendition.height), (300, 60))

    def test_un_svg_servi_depuis_media_interdit_les_scripts(self):
        from django.http import HttpResponse
        from django.test import RequestFactory
        from django.conf import settings
        from core.middleware import SvgSansScriptMiddleware
        middleware = SvgSansScriptMiddleware(lambda request: HttpResponse("<svg/>"))
        svg = middleware(RequestFactory().get(f"{settings.MEDIA_URL}original_images/logo.svg"))
        self.assertIn("sandbox", svg["Content-Security-Policy"])
        page = middleware(RequestFactory().get("/campagnes/"))
        self.assertNotIn("Content-Security-Policy", page)

    def test_logo_dore_devient_un_pochoir(self):
        from core.models import NavigationSettings
        reglages = NavigationSettings.load()
        reglages.logo_dore = True
        reglages.save()
        response = self.client.get(HomePage.objects.first().url)
        url = self.logo.get_rendition("max-320x96").url
        # L'image n'est plus un <img> : elle sert de masque, avec ses proportions
        self.assertContains(response, f"--logo-url: url('{url}')")
        self.assertContains(response, "aspect-ratio: 300.0 / 60.0")
        self.assertNotContains(response, 'class="site-logo"')


class EnluminureBlockTests(TestCase):
    def test_rendu_avec_l_ornement_choisi(self):
        from core.blocks import EnluminureBlock
        bloc = EnluminureBlock()
        html = bloc.render(bloc.to_python({"ornement": "marge", "texte": "<p>Il était une fois</p>"}))
        self.assertIn('class="enluminure enluminure--marge"', html)
        # La lettrine est faite en CSS : le mot reste entier dans le HTML
        self.assertIn("Il était une fois", html)


class BienDemarrerTests(TestCase):
    """La page « Bien démarrer » : structure du site en un clic, démo à ajouter / retirer."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        self.admin = get_user_model().objects.create_superuser("mj", "mj@example.com", "mdp")
        self.client.force_login(self.admin)

    def url(self):
        from django.urls import reverse
        return reverse("bien_demarrer")

    def test_cree_la_structure_sans_doublon(self):
        from campagnes.models import CampagnesIndexPage
        from encyclopedie.models import EncyclopedieIndexPage
        from pages.models import ContactPage, MentionsLegalesPage, UniversPage
        self.client.post(self.url(), {"action": "structure"})
        self.client.post(self.url(), {"action": "structure"})  # 2e clic : rien de plus
        for modele in (CampagnesIndexPage, EncyclopedieIndexPage, UniversPage, ContactPage, MentionsLegalesPage):
            self.assertEqual(modele.objects.count(), 1, modele.__name__)
        # Les mentions légales attendent leurs vraies informations : brouillon
        self.assertFalse(MentionsLegalesPage.objects.get().live)
        self.assertTrue(UniversPage.objects.get().live)
        # Le formulaire de contact a ses champs, et l'accueil pointe vers lui (menu)
        contact = ContactPage.objects.get()
        self.assertEqual(contact.form_fields.count(), 3)
        self.assertEqual(HomePage.objects.first().page_contact_id, contact.pk)
        self.assertContains(self.client.get(self.url()), "La structure est complète")
        # Accroche de départ : la page n'est pas vide et Google a une description
        self.assertContains(self.client.get(CampagnesIndexPage.objects.get().url),
                            '<meta name="description" content="Toutes nos campagnes de jeu de rôle')
        self.assertIn("maître du jeu", UniversPage.objects.get().intro)

    def test_ajoute_puis_retire_la_demo_avec_ses_images(self):
        from wagtail.images.models import Image
        from core.demo import CAMPAGNE, TAG_IMAGES
        from core.models import Categorie
        from campagnes.models import CampagnePage
        self.client.post(self.url(), {"action": "structure"})
        self.client.post(self.url(), {"action": "demo_ajouter"})
        self.assertTrue(CampagnePage.objects.filter(title=CAMPAGNE).exists())
        # Les 3 icônes SVG livrées avec la démo : importées, rangées, posées sur les catégories
        icone = Image.objects.get(title="Ville", tags__name=TAG_IMAGES)
        self.assertEqual(icone.collection.name, "Icône")
        self.assertEqual(icone.collection.get_parent().name, "Site")
        self.assertEqual(Categorie.objects.get(nom="Ville").icone, icone)

        self.client.post(self.url(), {"action": "demo_retirer"})
        self.assertFalse(CampagnePage.objects.filter(title=CAMPAGNE).exists())
        self.assertFalse(Image.objects.filter(tags__name=TAG_IMAGES).exists())
        self.assertIsNone(Categorie.objects.get(nom="Ville").icone)  # la catégorie reste, sans icône

    def test_demo_impossible_sans_structure(self):
        response = self.client.post(self.url(), {"action": "demo_ajouter"}, follow=True)
        self.assertContains(response, "Il faut d&#x27;abord les pages")

    def test_reservee_aux_administrateurs(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        redacteur = get_user_model().objects.create_user("redac", "r@example.com", "mdp")
        redacteur.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.client.force_login(redacteur)
        # Wagtail transforme le refus (PermissionDenied) en retour au tableau de bord
        self.assertRedirects(self.client.get(self.url()), "/admin/", fetch_redirect_response=False)
        # … et le bouton n'a rien créé
        self.client.post(self.url(), {"action": "structure"})
        from campagnes.models import CampagnesIndexPage
        self.assertFalse(CampagnesIndexPage.objects.exists())


class ReferencementTests(TestCase):
    def test_robots_txt_indique_le_plan_du_site(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        texte = response.content.decode()
        self.assertIn("Disallow: /admin/", texte)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", texte)

    def test_le_plan_du_site_suit_les_publications(self):
        from campagnes.models import CampagnesIndexPage
        index = HomePage.objects.first().add_child(instance=CampagnesIndexPage(title="Campagnes"))
        self.assertContains(self.client.get("/sitemap.xml"), "/campagnes/")
        index.unpublish()
        self.assertNotContains(self.client.get("/sitemap.xml"), "/campagnes/")


class ImagesDeLaDemoTests(TestCase):
    """Chaque fiche de la démo retrouve SON image, et le point focal est posé."""

    def test_chaque_fiche_a_une_image_declaree(self):
        from core import demo
        titres = ([("lieu", t) for t in demo.LIEUX] + [("lore", t) for t in demo.LORE]
                  + [("heros", t) for t in demo.HEROS])
        for prefixe, titre in titres:
            if titre == "Notes du MJ":
                continue  # fiche de texte seul, volontairement sans illustration
            self.assertIn(f"{prefixe}-{demo.slug_de_fichier(titre)}", demo.IMAGES, titre)

    def test_les_ligatures_ne_disparaissent_pas(self):
        from core.demo import slug_de_fichier
        self.assertEqual(slug_de_fichier("Sœur Ysolde"), "soeur-ysolde")  # slugify seul : « sur-ysolde »

    def test_le_point_focal_est_converti_en_pixels(self):
        from wagtail.images.models import Image
        from wagtail.images.tests.utils import get_test_image_file
        from core.demo import poser_le_point_focal
        image = Image.objects.create(title="Pip", file=get_test_image_file())  # 640 x 480
        poser_le_point_focal(image, "heros-pip-chardon")  # (50, 46, 20, 15) en %
        image.refresh_from_db()
        self.assertEqual((image.focal_point_x, image.focal_point_y), (320, 221))
        self.assertEqual((image.focal_point_width, image.focal_point_height), (128, 72))


class CouleursAdminTests(TestCase):
    """L'admin Wagtail prend les couleurs du thème du site (core/couleurs_admin.py)."""

    def test_chaque_theme_a_ses_couleurs_lisibles(self):
        from core.couleurs_admin import COULEURS_ADMIN, contraste_avec_le_blanc
        from core.models import THEMES
        for cle, _ in THEMES:
            self.assertIn(cle, COULEURS_ADMIN, f"Thème {cle!r} sans couleurs d'admin")
            for couleur in COULEURS_ADMIN[cle]:
                # Texte blanc sur le menu et sur les boutons : WCAG AA
                self.assertGreaterEqual(contraste_avec_le_blanc(couleur), 4.5, f"{cle} : {couleur}")

    def test_la_palette_du_site_par_defaut_est_lisible(self):
        """
        La palette de structure.css (thème « Aucun ») : texte blanc sur l'ocre
        (boutons, panneaux) et titres ocre sur fond blanc, au moins 4,5:1.
        On lit les variables directement dans le fichier CSS.
        """
        import re
        from pathlib import Path
        from django.conf import settings
        from core.couleurs_admin import contraste_avec_le_blanc
        css = (Path(settings.PROJECT_DIR) / "static" / "css" / "structure.css").read_text(encoding="utf-8")
        variables = dict(re.findall(r"(--color-[\w-]+):\s*(#[0-9A-Fa-f]{6})", css))
        self.assertEqual(variables["--color-accent-text"].upper(), "#FFFFFF")
        self.assertEqual(variables["--color-bg"].upper(), "#FFFFFF")
        for nom in ("--color-accent", "--color-title"):
            self.assertGreaterEqual(contraste_avec_le_blanc(variables[nom]), 4.5, f"{nom} : {variables[nom]}")

    def test_conversion_en_teinte_saturation_luminosite(self):
        from core.couleurs_admin import en_hsl
        self.assertEqual(en_hsl("#FF0000"), (0.0, 100.0, 50.0))
        self.assertEqual(en_hsl("#000000"), (0.0, 0.0, 0.0))

    def test_l_admin_recoit_les_couleurs_du_theme_choisi(self):
        from django.contrib.auth import get_user_model
        from core.couleurs_admin import css_couleurs_admin
        from core.models import NavigationSettings
        reglages = NavigationSettings.load()
        reglages.theme = "grimoire"
        reglages.save()
        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        self.assertContains(self.client.get("/admin/"), css_couleurs_admin("grimoire"))

    def test_l_admin_porte_le_logo_et_le_nom_du_site(self):
        from django.contrib.auth import get_user_model
        from wagtail.images.models import Image
        from wagtail.images.tests.utils import get_test_image_file
        from core.models import NavigationSettings
        # Sans logo choisi : le monogramme Tales Omnibus (logo par défaut, en pochoir)
        self.assertContains(self.client.get("/admin/login/"), "img/logo-tales-omnibus.svg")
        reglages = NavigationSettings.load()
        reglages.site_name = "Les Brumes"
        reglages.logo = Image.objects.create(title="Logo", file=get_test_image_file())
        reglages.save()
        connexion = self.client.get("/admin/login/")
        self.assertContains(connexion, "Se connecter à Les Brumes")
        self.assertContains(connexion, 'class="logo-du-site-admin"')
        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        tableau = self.client.get("/admin/")
        self.assertContains(tableau, "<title>Tableau de bord - Les Brumes</title>", html=False)
        self.assertContains(tableau, 'class="logo-du-site-admin"')

    def test_logo_par_defaut_et_logo_dore(self):
        """
        Sans logo choisi, le site affiche le monogramme Tales Omnibus en pochoir.
        Un logo « doré » est aussi un pochoir dans l'admin, rempli à la couleur
        du thème (sinon une silhouette noire disparaîtrait sur l'admin sombre).
        """
        from wagtail.images.models import Image
        from wagtail.images.tests.utils import get_test_image_file
        from core.couleurs_admin import LOGO_ADMIN
        from core.models import THEMES, NavigationSettings
        accueil = self.client.get("/")
        self.assertContains(accueil, "site-logo--dore")
        self.assertContains(accueil, "img/logo-tales-omnibus.svg")
        reglages = NavigationSettings.load()
        reglages.logo = Image.objects.create(title="Logo", file=get_test_image_file())
        reglages.logo_dore = True
        reglages.save()
        connexion = self.client.get("/admin/login/")
        self.assertContains(connexion, "logo-du-site-admin--dore")
        self.assertNotContains(connexion, "img/logo-tales-omnibus.svg")  # c'est SON logo qui s'affiche
        # Chaque thème a la couleur de logo de son admin
        for cle, _ in THEMES:
            self.assertIn(cle, LOGO_ADMIN, f"Thème {cle!r} sans couleur de logo d'admin")


class PolicesDesThemesTests(TestCase):
    """RGPD : polices chez Google (signalé) ou hébergées sur le site (core/polices.py)."""

    CSS_GOOGLE = (
        "/* cyrillic */\n@font-face {\n  font-family: 'Cinzel';\n"
        "  src: url(https://fonts.gstatic.com/s/cinzel/v1/c.woff2) format('woff2');\n}\n"
        "/* latin-ext */\n@font-face {\n  font-family: 'Cinzel';\n"
        "  src: url(https://fonts.gstatic.com/s/cinzel/v1/e.woff2) format('woff2');\n}\n"
        "/* latin */\n@font-face {\n  font-family: 'Cinzel';\n"
        "  src: url(https://fonts.gstatic.com/s/cinzel/v1/l.woff2) format('woff2');\n}\n"
        "/* latin */\n@font-face {\n  font-family: 'Cinzel';\n  font-weight: 700;\n"
        "  src: url(https://fonts.gstatic.com/s/cinzel/v1/l.woff2) format('woff2');\n}\n"
    )

    def test_seuls_les_alphabets_du_francais_sont_gardes(self):
        from core.polices import garder_les_alphabets_utiles
        blocs = garder_les_alphabets_utiles(self.CSS_GOOGLE)
        self.assertEqual(len(blocs), 3)  # latin-ext + 2 latin, sans le cyrillique
        self.assertFalse(any("c.woff2" in bloc for bloc in blocs))

    def test_la_commande_heberge_les_polices_du_theme(self):
        import io
        import tempfile
        from pathlib import Path
        from unittest import mock
        from django.core.management import call_command
        with tempfile.TemporaryDirectory() as dossier:
            theme = Path(dossier) / "css" / "themes" / "grimoire.css"
            theme.parent.mkdir(parents=True)
            theme.write_text('@import url("https://fonts.googleapis.com/css2?family=Cinzel&display=swap");\nbody {}\n',
                             encoding="utf-8")

            def faux_telechargement(url):
                return self.CSS_GOOGLE.encode() if "googleapis" in url else b"POLICE"

            module = "core.management.commands.heberger_polices"
            with mock.patch(f"{module}.chemin_du_theme", return_value=str(theme)), \
                    mock.patch(f"{module}.telecharger", side_effect=faux_telechargement) as telecharger:
                call_command("heberger_polices", "--theme", "grimoire", stdout=io.StringIO())
            polices = Path(dossier) / "fonts" / "grimoire"
            # 1 feuille + 2 fichiers (le fichier « latin » sert à deux graisses : téléchargé une fois)
            self.assertEqual(sorted(p.name for p in polices.iterdir()),
                             ["cinzel-1.woff2", "cinzel-2.woff2", "polices.css"])
            self.assertEqual(telecharger.call_count, 3)
            self.assertNotIn("gstatic", (polices / "polices.css").read_text(encoding="utf-8"))
            texte = theme.read_text(encoding="utf-8")
            self.assertIn('@import url("../../fonts/grimoire/polices.css");', texte)
            self.assertNotIn("googleapis", texte)

    def test_mentions_legales_signalent_google_fonts(self):
        from unittest import mock
        from home.models import HomePage
        from pages.models import MentionsLegalesPage
        page = HomePage.objects.first().add_child(instance=MentionsLegalesPage(
            title="Mentions légales", editeur_nom="X", editeur_email="x@example.com",
            hebergeur_nom="H", hebergeur_adresse="Paris",
        ))
        with mock.patch("pages.models.theme_utilise_google_fonts", return_value=True):
            self.assertContains(self.client.get(page.url), "fournies par Google Fonts")
        with mock.patch("pages.models.theme_utilise_google_fonts", return_value=False):
            self.assertNotContains(self.client.get(page.url), "Google Fonts")


class PoidsDesImagesTests(TestCase):
    """SEO / vitesse : les vignettes fabriquées par Wagtail sont en WebP."""

    def test_une_image_png_donne_des_vignettes_webp(self):
        from wagtail.images.models import Image
        from wagtail.images.tests.utils import get_test_image_file
        image = Image.objects.create(title="Test", file=get_test_image_file())  # un PNG
        self.assertTrue(image.file.name.endswith(".png"))  # l'original n'est pas touché
        self.assertTrue(image.get_rendition("fill-100x100").file.name.endswith(".webp"))
