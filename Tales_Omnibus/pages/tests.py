from django.core import mail
from django.test import TestCase
from home.models import HomePage

from pages.models import ContactFormField, ContactPage


class ContactPageTests(TestCase):
    def setUp(self):
        home = HomePage.objects.first()
        self.contact = home.add_child(instance=ContactPage(
            title="Contact", slug="contact-test",
            to_address="moi@example.com", from_address="site@example.com",
            subject="Nouveau message",
        ))
        for i, (label, field_type) in enumerate([('Nom', 'singleline'), ('Email', 'email'), ('Message', 'multiline')]):
            ContactFormField.objects.create(page=self.contact, sort_order=i, label=label,
                                            field_type=field_type, required=True)

    def test_la_page_affiche_les_champs(self):
        response = self.client.get(self.contact.url)
        self.assertContains(response, 'form-group--nom')
        # Le textarea reçoit la classe qui le place dans la colonne de droite
        self.assertContains(response, 'form-group--message')

    def test_envoi_affiche_la_page_de_remerciement(self):
        response = self.client.post(self.contact.url, {
            'nom': "Alice", 'email': "alice@example.com", 'message': "Coucou",
        })
        self.assertTemplateUsed(response, 'pages/contact_page_landing.html')
        self.assertContains(response, "Message envoyé !")
        self.assertContains(response, 'panel--accent')  # même mise en page que la page contact
        self.assertEqual(len(mail.outbox), 1)


class PrestationsTests(TestCase):
    def setUp(self):
        from pages.models import Prestation
        self.home = HomePage.objects.first()
        self.contact = self.home.add_child(instance=ContactPage(title="Contact", slug="contact-presta"))
        self.home.page_contact = self.contact
        self.home.save_revision().publish()
        self.Prestation = Prestation

    def test_pas_de_prestation_pas_de_section(self):
        self.assertNotContains(self.client.get(self.contact.url), "Mes prestations")

    def test_page_contact_detail_et_ordre(self):
        self.Prestation.objects.create(titre="One-shot", prix="Sur devis", ordre=2)
        self.Prestation.objects.create(titre="Campagne", description="<p>Dix séances</p>", ordre=1)
        html = self.client.get(self.contact.url).content.decode()
        self.assertIn("Dix séances", html)  # description visible sur la page Contact
        self.assertLess(html.index("Campagne"), html.index("One-shot"))  # ordre respecté

    def test_accueil_version_courte(self):
        self.Prestation.objects.create(titre="Initiation", description="<p>Détail long</p>", prix="Gratuit")
        response = self.client.get(self.home.url)
        self.assertContains(response, "Initiation")
        self.assertContains(response, "Gratuit")
        self.assertNotContains(response, "Détail long")  # le détail reste sur la page Contact


class MentionsLegalesTests(TestCase):
    def setUp(self):
        from pages.models import MentionsLegalesPage
        self.home = HomePage.objects.first()
        self.page = self.home.add_child(instance=MentionsLegalesPage(
            title="Mentions légales",
            editeur_nom="Jean Conteur", editeur_email="jean@example.com",
            hebergeur_nom="Hébergeur SAS", hebergeur_adresse="1 rue du Serveur, Paris",
        ))
        # Publiée comme dans l'admin : c'est ce qui date la « dernière mise à jour »
        self.page.save_revision().publish()

    def test_slug_fixe_et_lien_dans_le_pied_de_page(self):
        self.assertEqual(self.page.slug, "mentions-legales")
        self.assertContains(self.client.get(self.home.url), 'href="/mentions-legales/"')

    def test_inserts_automatiques(self):
        html = self.client.get(self.page.url).content.decode()
        self.assertIn("Jean Conteur", html)
        self.assertIn("http://testserver/", html)  # adresse du site, déduite de la requête
        self.assertIn("Directeur de la publication : Jean Conteur", html)  # défaut = l'éditeur
        self.assertIn("Dernière mise à jour", html)
        self.assertNotIn("SIRET", html)  # vide : la ligne n'apparaît pas

    def test_lien_vers_la_page_contact(self):
        contact = self.home.add_child(instance=ContactPage(title="Écris-moi", slug="x"))
        self.home.page_contact = contact
        self.home.save_revision().publish()
        self.assertContains(self.client.get(self.page.url), "page Écris-moi")

    def test_cookies_du_lecteur_live_signales_seulement_s_il_existe(self):
        self.assertNotContains(self.client.get(self.page.url), "intègre un lecteur")
        self.home.stream_player = [('lecteur', {'plateforme': 'youtube', 'chaine': 'UC' + 'a' * 22, 'titre': ''})]
        self.home.save_revision().publish()
        self.assertContains(self.client.get(self.page.url), "intègre un lecteur YouTube")

    def test_une_seule_page_de_mentions(self):
        from pages.models import MentionsLegalesPage
        self.assertFalse(MentionsLegalesPage.can_create_at(self.home))
