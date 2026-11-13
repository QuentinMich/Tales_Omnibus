from django.core import mail
from django.test import TestCase
from home.models import HomePage

from campagnes.models import (
    CampagnePage, CampagnesIndexPage, ChronologiePage, EvenementPage, HeroPage,
)


class CampagneTreeMixin:
    """Construit une petite arborescence : Accueil > Campagnes > Campagne."""

    def setUp(self):
        home = HomePage.objects.first()
        self.index = home.add_child(instance=CampagnesIndexPage(title="Campagnes"))
        self.campagne = self.index.add_child(instance=CampagnePage(title="Saison 1"))


class HeroContactTests(CampagneTreeMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.hero = self.campagne.add_child(instance=HeroPage(
            title="Aldric", joueur_nom="Bob",
            joueur_email="joueur@example.com", enable_contact=True,
        ))

    def post(self, **data):
        payload = {'nom': "Alice", 'email': "alice@example.com",
                   'raison': 'rp', 'message': "Salut !"}
        payload.update(data)
        return self.client.post(self.hero.url, payload, follow=True)

    def test_message_valide_envoye_au_joueur(self):
        response = self.post()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["joueur@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["alice@example.com"])
        self.assertContains(response, "bien été envoyé")

    def test_formulaire_invalide_affiche_les_erreurs(self):
        response = self.post(email="pas-un-email")
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, "errorlist")

    def test_pas_de_formulaire_sans_email_joueur(self):
        self.hero.joueur_email = ""
        self.hero.save_revision().publish()
        response = self.client.get(self.hero.url)
        self.assertNotContains(response, "hero-contact-form")


class ChronologieTests(CampagneTreeMixin, TestCase):
    def test_evenements_tries_par_date_ordre(self):
        chrono = self.campagne.add_child(instance=ChronologiePage(title="Frise"))
        for titre, date in [("Couronnement", 1200), ("Fondation", -50), ("Guerre", 800)]:
            chrono.add_child(instance=EvenementPage(title=titre, date_ordre=date))

        response = self.client.get(chrono.url)
        titres = [e.title for e in response.context['evenements']]
        self.assertEqual(titres, ["Fondation", "Guerre", "Couronnement"])

    def test_campagne_affiche_sa_chronologie(self):
        self.campagne.add_child(instance=ChronologiePage(title="Frise"))
        response = self.client.get(self.campagne.url)
        self.assertContains(response, "Consulter la chronologie")


class LieuDesFichesTests(CampagneTreeMixin, TestCase):
    """Le "pin" : un héros / un événement pointe vers un Lieu existant."""

    def setUp(self):
        super().setUp()
        from campagnes.models import Apparition, CartePage, LieuPage
        from encyclopedie.models import EncyclopedieIndexPage
        self.encyclopedie = self.index.get_parent().add_child(instance=EncyclopedieIndexPage(title="Encyclopédie"))
        self.clairiere = self.encyclopedie.add_child(instance=LieuPage(title="Clairière déserte"))
        self.carte = self.campagne.add_child(instance=CartePage(title="Royaume"))
        Apparition.objects.create(carte=self.carte, lieu=self.clairiere, coord_x=12.5, coord_y=40)
        chrono = self.campagne.add_child(instance=ChronologiePage(title="Frise"))
        self.bataille = chrono.add_child(instance=EvenementPage(title="La bataille", lieu=self.clairiere))
        self.hero = self.campagne.add_child(instance=HeroPage(
            title="Aldric", joueur_nom="Bob", lieu_origine=self.clairiere))

    def test_la_fiche_evenement_affiche_la_mini_carte(self):
        response = self.client.get(self.bataille.url)
        self.assertContains(response, "Lieu de l'événement")
        self.assertContains(response, "carte-mini")
        self.assertContains(response, "--x: 12.5")  # |unlocalize : un point, pas une virgule
        self.assertContains(response, self.clairiere.url)

    def test_la_fiche_heros_affiche_son_lieu_d_origine(self):
        self.assertContains(self.client.get(self.hero.url), "Lieu d'origine")

    def test_la_fiche_lieu_liste_ce_qui_s_y_rattache(self):
        response = self.client.get(self.clairiere.url)
        self.assertContains(response, "Liés à ce lieu")
        self.assertContains(response, "La bataille")
        self.assertContains(response, "Aldric")

    def test_lieu_depublie_pas_de_mini_carte(self):
        self.clairiere.unpublish()
        self.assertNotContains(self.client.get(self.bataille.url), "carte-mini")

    def test_pas_de_doublon_avec_les_fiches_liees(self):
        # La bataille partage un tag avec la clairière ET y est rattachée :
        # elle ne doit apparaître qu'une fois, dans « Liés à ce lieu ».
        for page in (self.clairiere, self.bataille):
            page.tags.add("guerre")
            page.save_revision().publish()
        html = self.client.get(self.clairiere.url).content.decode()
        self.assertEqual(html.count(f'href="{self.bataille.url}"'), 1)



class ApparitionsTests(CampagneTreeMixin, TestCase):
    """
    Un même lieu sur plusieurs cartes, dans deux campagnes :
      Saison 1 > carte « Royaume »     : Caer Fiodh en (10, 20), « caché par le brouillard »
      Saison 2 > carte « Monde »       : Caer Fiodh en (60, 70)
    """

    def setUp(self):
        super().setUp()
        from campagnes.models import Apparition, CartePage, LieuPage
        from encyclopedie.models import EncyclopedieIndexPage
        self.encyclopedie = self.index.get_parent().add_child(instance=EncyclopedieIndexPage(title="Encyclopédie"))
        self.caer = self.encyclopedie.add_child(instance=LieuPage(title="Caer Fiodh"))
        self.saison2 = self.index.add_child(instance=CampagnePage(title="Saison 2"))
        self.royaume = self.campagne.add_child(instance=CartePage(title="Royaume"))
        self.monde = self.saison2.add_child(instance=CartePage(title="Monde"))
        Apparition.objects.create(carte=self.royaume, lieu=self.caer, coord_x=10, coord_y=20,
                                  a_cette_epoque="Caché par le brouillard")
        Apparition.objects.create(carte=self.monde, lieu=self.caer, coord_x=60, coord_y=70)

    def test_chaque_carte_place_le_lieu_a_sa_position(self):
        self.assertContains(self.client.get(self.royaume.url), "--x: 10")
        self.assertContains(self.client.get(self.monde.url), "--x: 60")

    def test_la_fiche_lieu_montre_toutes_ses_cartes(self):
        response = self.client.get(self.caer.url)
        self.assertContains(response, "Sur les cartes")
        self.assertContains(response, "Royaume")
        self.assertContains(response, "Monde")
        self.assertContains(response, "Caché par le brouillard")

    def test_le_heros_voit_le_lieu_depuis_sa_campagne(self):
        # Héros de la Saison 2 : on doit lui montrer la carte du Monde, pas le Royaume
        hero = self.saison2.add_child(instance=HeroPage(title="Brune", joueur_nom="Zoé", lieu_origine=self.caer))
        self.assertEqual(self.caer.apparition_vue_depuis(hero).carte.pk, self.monde.pk)
        self.assertContains(self.client.get(hero.url), "--x: 60")

    def test_le_lieu_appartient_aux_deux_campagnes(self):
        from encyclopedie.models import requetes_de_fiches
        accueil = self.index.get_parent()
        for campagne in (self.campagne, self.saison2):
            lieux = dict(requetes_de_fiches(accueil, campagne, 'lieux'))['lieux']
            self.assertEqual([l.title for l in lieux], ["Caer Fiodh"])

    def test_lieu_pas_encore_place_pas_d_etoile(self):
        from campagnes.models import Apparition
        Apparition.objects.filter(carte=self.monde).update(coord_x=None, coord_y=None)
        response = self.client.get(self.monde.url)
        self.assertNotContains(response, 'class="map-marker"')
        self.assertContains(response, "Caer Fiodh")  # mais bien listé sous la carte


class RangerLieuxTests(CampagneTreeMixin, TestCase):
    def test_la_commande_range_les_lieux_dans_l_encyclopedie(self):
        from io import StringIO
        from django.core.management import call_command
        from campagnes.models import CartePage, LieuPage
        from encyclopedie.models import EncyclopedieIndexPage
        encyclopedie = self.index.get_parent().add_child(instance=EncyclopedieIndexPage(title="Encyclopédie"))
        carte = self.campagne.add_child(instance=CartePage(title="Royaume"))
        # Un lieu "à l'ancienne", sous une carte (on force : ce n'est plus permis dans l'admin)
        lieu = carte.add_child(instance=LieuPage(title="Vieux moulin"))
        call_command('ranger_lieux', stdout=StringIO())
        lieu.refresh_from_db()
        self.assertEqual(lieu.get_parent().pk, encyclopedie.pk)
        # Relancée, elle ne fait rien
        sortie = StringIO()
        call_command('ranger_lieux', stdout=sortie)
        self.assertIn("déjà", sortie.getvalue())


class GeometrieTests(TestCase):
    """Les fonctions pures de campagnes/geometrie.py : des nombres, pas de base."""

    CARRE = [[0, 0], [10, 0], [10, 10], [0, 10]]

    def test_aire_et_centre_d_un_carre(self):
        from campagnes.geometrie import aire, centre
        self.assertEqual(aire(self.CARRE), 100)
        self.assertEqual(centre(self.CARRE), (5, 5))
        # Le sens de rotation (horaire ou non) ne change pas l'aire
        self.assertEqual(aire(list(reversed(self.CARRE))), 100)

    def test_point_dedans_ou_dehors(self):
        from campagnes.geometrie import contient
        self.assertTrue(contient(self.CARRE, 5, 5))
        self.assertFalse(contient(self.CARRE, 15, 5))
        # Une forme en L (concave) : le creux du L est DEHORS
        en_l = [[0, 0], [10, 0], [10, 4], [4, 4], [4, 10], [0, 10]]
        self.assertTrue(contient(en_l, 2, 8))
        self.assertFalse(contient(en_l, 8, 8))

    def test_ranger_choisit_la_plus_petite_zone(self):
        from campagnes.geometrie import ranger
        parents = ranger([
            {'cle': 'royaume', 'lieu': 1, 'point': (50, 50), 'zone': [[0, 0], [100, 0], [100, 100], [0, 100]]},
            {'cle': 'duche', 'lieu': 2, 'point': (25, 25), 'zone': [[10, 10], [40, 10], [40, 40], [10, 40]]},
            {'cle': 'ville', 'lieu': 3, 'point': (20, 20), 'zone': None},
            {'cle': 'port', 'lieu': 4, 'point': (80, 80), 'zone': None},
            {'cle': 'perdu', 'lieu': 5, 'point': None, 'zone': None},
        ])
        self.assertEqual(parents, {'royaume': None, 'duche': 'royaume', 'ville': 'duche',
                                   'port': 'royaume', 'perdu': None})

    def test_un_lieu_n_est_pas_dans_lui_meme(self):
        from campagnes.geometrie import ranger
        parents = ranger([
            {'cle': 'zone', 'lieu': 1, 'point': (5, 5), 'zone': self.CARRE},
            {'cle': 'etoile', 'lieu': 1, 'point': (5, 5), 'zone': None},  # même lieu, dessiné 2 fois
        ])
        self.assertIsNone(parents['etoile'])

    def test_forme_valide(self):
        from campagnes.geometrie import est_une_forme_valide
        self.assertTrue(est_une_forme_valide(self.CARRE))
        self.assertFalse(est_une_forme_valide([[0, 0], [10, 10]]))            # 2 coins : une ligne
        self.assertFalse(est_une_forme_valide([[0, 0], [10, 0], [150, 10]]))  # hors de l'image
        self.assertFalse(est_une_forme_valide("pas une liste"))


class ZonesTests(CampagneTreeMixin, TestCase):
    """
    Sur la carte « Monde » : la zone Ardenn, la zone Bois (dans Ardenn),
    le point Hameau (dans le Bois) et le point Large (hors de tout).
    """

    def setUp(self):
        super().setUp()
        from campagnes.models import Apparition, CartePage, LieuPage
        from encyclopedie.models import EncyclopedieIndexPage
        encyclopedie = self.index.get_parent().add_child(instance=EncyclopedieIndexPage(title="Encyclopédie"))
        self.lieux = {nom: encyclopedie.add_child(instance=LieuPage(title=nom))
                      for nom in ("Ardenn", "Bois", "Hameau", "Large")}
        self.carte = self.campagne.add_child(instance=CartePage(title="Monde"))
        for nom, forme, x, y in [
            ("Ardenn", [[10, 10], [90, 10], [90, 90], [10, 90]], None, None),
            ("Bois", [[40, 40], [60, 40], [60, 60], [40, 60]], None, None),
            ("Hameau", None, 50, 50),
            ("Large", None, 95, 5),
        ]:
            Apparition.objects.create(carte=self.carte, lieu=self.lieux[nom], forme=forme, coord_x=x, coord_y=y)
        self.carte.save_revision().publish()  # la publication range les lieux

    def apparition(self, nom):
        from campagnes.models import Apparition
        return Apparition.objects.get(carte=self.carte, lieu=self.lieux[nom])

    def test_la_publication_range_les_lieux(self):
        self.assertIsNone(self.apparition("Ardenn").contenu_dans)
        self.assertEqual(self.apparition("Bois").contenu_dans, self.lieux["Ardenn"])
        self.assertEqual(self.apparition("Hameau").contenu_dans, self.lieux["Bois"])
        self.assertIsNone(self.apparition("Large").contenu_dans)

    def test_l_etoile_d_une_zone_est_son_centre(self):
        bois = self.apparition("Bois")
        self.assertEqual((bois.coord_x, bois.coord_y), (50, 50))

    def test_un_centre_place_a_la_main_est_garde(self):
        carte = self.carte.get_latest_revision_as_object()
        bois = next(a for a in carte.apparitions.all() if a.lieu_id == self.lieux["Bois"].pk)
        bois.coord_x, bois.coord_y, bois.centre_manuel = 42, 58, True
        carte.save_revision().publish()
        bois = self.apparition("Bois")
        self.assertEqual((bois.coord_x, bois.coord_y), (42, 58))  # pas écrasé par (50, 50)
        self.assertEqual(bois.contenu_dans, self.lieux["Ardenn"])

    def test_un_centre_hors_de_la_zone_est_refuse(self):
        from django.core.exceptions import ValidationError
        bois = self.apparition("Bois")
        bois.coord_x, bois.coord_y, bois.centre_manuel = 5, 5, True
        with self.assertRaises(ValidationError):
            bois.full_clean()

    def test_le_chemin_va_du_plus_grand_au_plus_proche(self):
        self.assertEqual([l.title for l in self.apparition("Hameau").chemin()], ["Ardenn", "Bois"])

    def test_deplacer_un_point_le_change_de_zone(self):
        # On sort le hameau du bois (mais il reste dans Ardenn), puis on republie
        carte = self.carte.get_latest_revision_as_object()
        hameau = next(a for a in carte.apparitions.all() if a.lieu_id == self.lieux["Hameau"].pk)
        hameau.coord_x, hameau.coord_y = 20, 20
        carte.save_revision().publish()
        self.assertEqual(self.apparition("Hameau").contenu_dans, self.lieux["Ardenn"])

    def test_la_page_carte_dessine_les_zones(self):
        response = self.client.get(self.carte.url)
        self.assertContains(response, 'class="carte-zones"')
        self.assertContains(response, 'points="10,10 90,10 90,90 10,90"')
        self.assertContains(response, 'class="map-zone-nom"')
        # La plus grande zone d'abord : le Bois passe au-dessus d'Ardenn
        html = response.content.decode()
        self.assertLess(html.index('points="10,10'), html.index('points="40,40'))

    def test_les_fiches_montrent_la_geographie(self):
        hameau = self.client.get(self.lieux["Hameau"].url)
        self.assertContains(hameau, "Situé dans")
        ardenn = self.client.get(self.lieux["Ardenn"].url)
        self.assertContains(ardenn, "Dans ce lieu")
        # Un seul niveau, comme un dossier : le Bois est dans Ardenn,
        # le Hameau est dans le Bois (on le voit sur la fiche du Bois)
        self.assertContains(ardenn, "/encyclopedie/bois/")
        self.assertNotContains(ardenn, "/encyclopedie/hameau/")
        self.assertContains(self.client.get(self.lieux["Bois"].url), "/encyclopedie/hameau/")

    def test_une_zone_de_deux_coins_est_refusee(self):
        from django.core.exceptions import ValidationError
        from campagnes.models import Apparition
        apparition = Apparition(carte=self.carte, lieu=self.lieux["Large"], forme=[[0, 0], [10, 10]])
        with self.assertRaises(ValidationError):
            apparition.full_clean()


class EditeurDeCarteAdminTests(CampagneTreeMixin, TestCase):
    def setUp(self):
        super().setUp()
        from django.contrib.auth import get_user_model
        from campagnes.models import CartePage
        self.carte = self.campagne.add_child(instance=CartePage(title="Monde"))
        admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "x")
        self.client.force_login(admin)

    def test_le_formulaire_contient_l_editeur(self):
        from django.urls import reverse
        response = self.client.get(reverse("wagtailadmin_pages:edit", args=[self.carte.pk]))
        self.assertContains(response, "data-editeur-carte")
        self.assertContains(response, "campagnes/js/editeur_carte.js")
        self.assertContains(response, 'data-outil="zone"')  # dans le modèle de ligne vide

    def test_la_vue_donne_l_image_non_recadree(self):
        from django.urls import reverse
        from wagtail.images import get_image_model
        from wagtail.images.tests.utils import get_test_image_file
        image = get_image_model().objects.create(title="Carte", file=get_test_image_file())
        response = self.client.get(reverse("image_de_carte", args=[image.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("width-1400", response.json()["url"])
