from django import template

from core.models import NavigationSettings
from core.seo import description_seo, image_seo, titre_seo

register = template.Library()


@register.simple_tag(takes_context=True)
def seo_de_la_page(context):
    """
    Tout ce qu'il faut pour le <head> de base.html :
    {% seo_de_la_page as seo %} puis seo.titre, seo.description, seo.image, seo.url.
    """
    request = context.get('request')
    page = context.get('page')
    if page is not None:
        page = page.specific  # pour avoir intro, catégorie… du vrai type de page
    nom_du_site = NavigationSettings.load(request_or_site=request).site_name if request else ""

    image = image_seo(page) if page is not None else None
    return {
        'titre': titre_seo(page, nom_du_site),
        'description': description_seo(page, nom_du_site),
        # Les réseaux sociaux veulent des adresses COMPLÈTES (https://…)
        'url': page.get_full_url(request) if page is not None and request else "",
        'image': request.build_absolute_uri(image.get_rendition('fill-1200x630').url) if image and request else "",
        'type': 'website' if page is None or page.depth <= 2 else 'article',
    }
