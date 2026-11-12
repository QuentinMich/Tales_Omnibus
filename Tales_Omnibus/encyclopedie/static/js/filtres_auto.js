/*
 * Filtres de l'encyclopédie : envoi automatique du formulaire.
 *
 * Sans JavaScript, le bouton « Filtrer » fait le travail (amélioration
 * progressive). Avec, dès qu'on change un menu ou qu'on clique un tag,
 * le formulaire part tout seul : le bouton devient inutile, on le cache.
 */
document.querySelectorAll('[data-filtres-auto]').forEach((formulaire) => {
    formulaire.addEventListener('change', () => formulaire.requestSubmit());
    formulaire.querySelector('button[type="submit"]')?.setAttribute('hidden', '');
});
