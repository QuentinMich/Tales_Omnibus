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
        from campagnes.models import CartePage, LieuPage
        carte = self.campagne.add_child(instance=CartePage(title="Royaume"))
        self.clairiere = carte.add_child(instance=LieuPage(title="Clairière déserte", coord_x=12.5, coord_y=40))
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
