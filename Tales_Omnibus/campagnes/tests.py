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
