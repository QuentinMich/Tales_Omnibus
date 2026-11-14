"""
LA STRUCTURE FIXE DU SITE, créée en un clic (page « Bien démarrer » de l'admin).

Le site a cinq pages « fixes », une seule de chaque, toutes sous l'accueil :
le menu et le pied de page les retrouvent par leur TYPE (jamais par leur
titre). Un nouveau MJ qui installe le site n'a pas à savoir lesquelles créer
ni où : un bouton le fait pour lui.

- On ne crée JAMAIS de doublon : une page déjà présente est laissée telle
  quelle (et signalée). On peut donc cliquer autant de fois qu'on veut.
- Les mentions légales sont créées en BROUILLON : leurs informations (éditeur,
  hébergeur…) sont obligatoires et seul le propriétaire du site les connaît.
  Publier de fausses mentions légales serait pire que de ne rien publier.
"""
from dataclasses import dataclass

from django.db import transaction
from wagtail.models import Site

from campagnes.models import CampagnesIndexPage
from encyclopedie.models import EncyclopedieIndexPage
from pages.models import ContactFormField, ContactPage, MentionsLegalesPage, UniversPage

A_COMPLETER = "À compléter"


@dataclass
class PageFixe:
    modele: type
    titre: str
    role: str  # à quoi elle sert, en une phrase (affiché dans l'admin)

    def page(self):
        """La page existante de ce type (publiée ou non), ou None."""
        return self.modele.objects.first()


PAGES_FIXES = [
    PageFixe(CampagnesIndexPage, "Campagnes", "la liste des campagnes (menu « Campagnes »)"),
    PageFixe(EncyclopedieIndexPage, "Encyclopédie", "les lieux, le Lore et toutes les fiches (menu « Encyclopédie »)"),
    PageFixe(UniversPage, "Univers", "la présentation du MJ et de son monde (menu « Univers »)"),
    PageFixe(ContactPage, "Contact", "le formulaire de contact (menu « Contact »)"),
    PageFixe(MentionsLegalesPage, "Mentions légales", "obligatoires pour un site public (lien du pied de page)"),
]

# Les champs du formulaire de la page Contact : (libellé, type de champ)
CHAMPS_DU_CONTACT = [("Nom", "singleline"), ("Email", "email"), ("Message", "multiline")]


def etat_de_la_structure():
    """[(PageFixe, page ou None)] : ce qui existe déjà, ce qui manque."""
    return [(fixe, fixe.page()) for fixe in PAGES_FIXES]


def structure_complete():
    return all(page for _, page in etat_de_la_structure())


def accueil():
    site = Site.objects.filter(is_default_site=True).select_related("root_page").first()
    return site.root_page.specific if site else None


def creer_structure(utilisateur=None):
    """Crée les pages fixes qui manquent. Renvoie la liste des phrases du compte rendu."""
    racine = accueil()
    if racine is None:
        return ["Aucun site par défaut : à configurer dans Paramètres avancés > Sites."]

    compte_rendu = []
    with transaction.atomic():
        for fixe, existante in etat_de_la_structure():
            if existante:
                compte_rendu.append(f"« {existante.title} » existe déjà : rien à faire.")
                continue
            page = _nouvelle_page(fixe)
            racine.add_child(instance=page)
            if isinstance(page, MentionsLegalesPage):
                page.save_revision(user=utilisateur)  # brouillon : à compléter avant publication
                compte_rendu.append("« Mentions légales » créée en BROUILLON : renseigne l'éditeur et "
                                    "l'hébergeur, puis publie-la (c'est une obligation légale).")
                continue
            if isinstance(page, ContactPage):
                for ordre, (libelle, type_de_champ) in enumerate(CHAMPS_DU_CONTACT):
                    ContactFormField.objects.create(page=page, sort_order=ordre, label=libelle,
                                                    field_type=type_de_champ, required=True)
            page.save_revision(user=utilisateur).publish(user=utilisateur)
            compte_rendu.append(f"« {page.title} » créée et publiée.")
        compte_rendu += _relier_le_contact_a_l_accueil(racine, utilisateur)
    return compte_rendu


def _nouvelle_page(fixe):
    if fixe.modele is MentionsLegalesPage:
        # Champs obligatoires : un texte qui saute aux yeux, en attendant les vrais
        return MentionsLegalesPage(
            title=fixe.titre, live=False, editeur_nom=A_COMPLETER, editeur_email="a-completer@example.com",
            hebergeur_nom=A_COMPLETER, hebergeur_adresse=A_COMPLETER,
        )
    if fixe.modele is ContactPage:
        return ContactPage(title=fixe.titre, subject="Nouveau message depuis le site",
                           intro="<p>Une question, une proposition de partie ? Écris-moi.</p>")
    return fixe.modele(title=fixe.titre)


def _relier_le_contact_a_l_accueil(racine, utilisateur):
    """Le menu trouve la page Contact grâce au champ « Page Contact » de l'accueil."""
    if not hasattr(racine, "page_contact") or racine.page_contact_id:
        return []
    contact = ContactPage.objects.first()
    if contact is None:
        return []
    if racine.has_unpublished_changes:
        # On ne publie pas à sa place un brouillon de l'accueil qu'il n'a pas fini
        return ["L'accueil a un brouillon en cours : choisis toi-même la page Contact dans "
                "son champ « Page Contact », puis publie-le."]
    racine.page_contact = contact
    racine.save_revision(user=utilisateur).publish(user=utilisateur)
    return ["L'accueil est relié à la page Contact (lien « Contact » du menu)."]
