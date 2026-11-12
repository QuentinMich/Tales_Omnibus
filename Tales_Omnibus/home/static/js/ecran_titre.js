/* ==========================================================================
   ÉCRAN TITRE DE L'ACCUEIL
   1. L'image d'ouverture + la nav remplissent exactement un écran.
   2. Une fois l'image dépassée en scrollant, on la retire de la page :
      la nav reste collée en haut et on ne peut plus remonter sur l'image.
   Sans JavaScript, la page reste utilisable : l'image ne disparaît juste pas.
   ========================================================================== */
(function () {
    const hero = document.querySelector('.home-hero');
    const header = document.querySelector('.site-header');
    if (!hero || !header) return;

    // 1. On transmet la hauteur du header au CSS (variable --header-height).
    //    ResizeObserver la remet à jour si le header change de taille
    //    (menu qui passe sur deux lignes sur mobile, par exemple).
    const majHauteurHeader = () => {
        document.documentElement.style.setProperty('--header-height', header.offsetHeight + 'px');
    };
    majHauteurHeader();
    new ResizeObserver(majHauteurHeader).observe(header);

    // 2. IntersectionObserver prévient quand l'image entre ou sort de l'écran.
    const guetteur = new IntersectionObserver(([entree]) => {
        const sortieParLeHaut = !entree.isIntersecting && entree.boundingClientRect.top < 0;
        if (!sortieParLeHaut) return;

        // On mémorise la position AVANT de retirer l'image...
        const hauteurImage = hero.offsetHeight;
        const position = window.scrollY;
        guetteur.disconnect();
        hero.remove();
        // ...puis on recale le scroll : le contenu ne bouge pas à l'écran.
        window.scrollTo({ top: Math.max(0, position - hauteurImage), behavior: 'instant' });
    });
    guetteur.observe(hero);
})();
