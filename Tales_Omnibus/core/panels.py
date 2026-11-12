"""Panneaux d'admin Wagtail réutilisables."""
from django.urls import reverse
from wagtail.admin.panels import Panel
from wagtail.models import Page


class ChildPagesPanel(Panel):
    """
    Affiche, dans le formulaire d'édition d'une page, la liste de ses pages
    enfants (avec lien "Modifier") et un bouton "Ajouter" par type autorisé.

    Usage : content_panels = [..., ChildPagesPanel(heading="Héros, cartes...")]
    C'est un panneau en lecture seule : il n'ajoute aucun champ au formulaire.
    """

    class BoundPanel(Panel.BoundPanel):
        template_name = "core/panels/child_pages_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            page = self.instance

            # Page en cours de création : elle n'existe pas encore en base,
            # donc elle ne peut pas avoir d'enfants.
            if not page.pk:
                context["is_new"] = True
                return context

            context["children"] = page.get_children().specific().order_by("path")
            # Un bouton par type de page autorisé ici (respecte subpage_types
            # et max_count grâce à can_create_at)
            context["creatable_types"] = [
                {
                    "label": model.get_verbose_name(),
                    "url": reverse("wagtailadmin_pages:add", args=[
                        model._meta.app_label, model._meta.model_name, page.pk,
                    ]),
                }
                for model in page.specific_class.allowed_subpage_models()
                if model.can_create_at(page)
            ]
            return context


def panels_avec_enfants(base_panels, heading, extra_panels=()):
    """
    Construit une liste content_panels avec ChildPagesPanel inséré juste
    après le titre, pour qu'il soit visible dès l'ouverture de la page.
    """
    nb_titre = len(Page.content_panels)
    return [
        *base_panels[:nb_titre],
        ChildPagesPanel(heading=heading, icon="folder-open-inverse"),
        *base_panels[nb_titre:],
        *extra_panels,
    ]
