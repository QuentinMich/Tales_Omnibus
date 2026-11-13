/*
 * FILTRE « AFFICHER » DE LA PAGE CARTE
 *
 * Chaque élément d'un lieu (étoile ou icône, zone, hachures, nom de zone,
 * ligne de la liste sous la carte) porte data-categories="8 10 11" : sa
 * catégorie ET tous ses ancêtres (Lieu › Village › Hameau). Choisir une
 * catégorie montre les éléments dont la liste la CONTIENT : choisir
 * « Village » montre donc aussi les hameaux (toute la branche, comme le
 * filtre de l'encyclopédie).
 *
 * Tout se passe dans le navigateur : pas de rechargement de la page.
 * Le choix est recopié dans l'adresse (?afficher=10) : on peut partager
 * le lien d'une carte « villages uniquement ».
 */
(function () {
    "use strict";

    const boite = document.querySelector("[data-filtre-carte]");
    if (!boite) return;

    const menu = boite.querySelector("select");
    const resultat = boite.querySelector("[data-filtre-resultat]");
    const elements = document.querySelectorAll("[data-categories]");
    const lignes = document.querySelectorAll("li[data-categories]");

    function appliquer() {
        const choix = menu.value;
        elements.forEach((element) => {
            const visible = !choix || element.dataset.categories.split(" ").includes(choix);
            // toggleAttribute et pas element.hidden : les zones sont des
            // éléments SVG, qui n'ont pas la propriété « hidden » du HTML.
            // L'attribut, lui, est caché par la règle [hidden] de structure.css.
            element.toggleAttribute("hidden", !visible);
        });

        if (choix) {
            const nombre = Array.from(lignes).filter((ligne) => !ligne.hidden).length;
            resultat.textContent = nombre > 1 ? `${nombre} lieux affichés` : `${nombre} lieu affiché`;
        } else {
            resultat.textContent = "";
        }

        // Le choix dans l'adresse, sans recharger ni ajouter d'étape à l'historique
        const adresse = new URL(window.location.href);
        if (choix) adresse.searchParams.set("afficher", choix);
        else adresse.searchParams.delete("afficher");
        window.history.replaceState(null, "", adresse);
    }

    // Arrivée par un lien partagé (?afficher=10) : on reprend ce choix
    const demande = new URL(window.location.href).searchParams.get("afficher");
    if (demande && menu.querySelector(`option[value="${CSS.escape(demande)}"]`)) {
        menu.value = demande;
    }

    menu.addEventListener("change", appliquer);
    boite.hidden = false; // le JS est là : on peut montrer le menu
    appliquer();
})();
