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
