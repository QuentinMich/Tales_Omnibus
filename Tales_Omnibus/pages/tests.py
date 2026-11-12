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
