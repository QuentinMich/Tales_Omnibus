/*
 * PLEIN ÉCRAN DE LA PAGE CARTE
 *
 * Met en plein écran le CADRE de la carte (image + zones + marqueurs), avec
 * l'API Fullscreen du navigateur. Échap fait sortir (géré par le navigateur).
 *
 * Le bouton est caché dans le HTML (hidden) et n'apparaît que si le
 * navigateur sait mettre un élément en plein écran : sur iPhone, par
 * exemple, il ne le sait pas, et un bouton qui ne fait rien serait pire
 * que pas de bouton.
 */
(function () {
    "use strict";

    const cadre = document.querySelector("[data-plein-ecran]");
    const bouton = document.querySelector("[data-plein-ecran-bouton]");
    if (!cadre || !bouton || !document.fullscreenEnabled) return;

    bouton.hidden = false;

    bouton.addEventListener("click", () => {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            cadre.requestFullscreen();
        }
    });

    // Le libellé suit l'état réel (on peut aussi sortir avec Échap)
    document.addEventListener("fullscreenchange", () => {
        const actif = document.fullscreenElement === cadre;
        bouton.textContent = actif ? "Quitter le plein écran" : "Plein écran";
        bouton.setAttribute("aria-pressed", String(actif));
    });
})();
