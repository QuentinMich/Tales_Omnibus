/*
 * VISIONNEUSE : cliquer sur une image pour l'agrandir.
 *
 * Dans le HTML, une image agrandissable est dans un lien vers sa grande
 * version : <a href="grande.jpg" data-agrandir><img alt="…"></a>.
 * Sans JavaScript, le lien ouvre simplement l'image en grand : ça marche
 * quand même. Avec JavaScript, on intercepte le clic et on l'ouvre dans un
 * <dialog>, la fenêtre native du navigateur : showModal() bloque le reste
 * de la page, la touche Échap ferme, et le focus clavier est géré pour nous
 * (accessibilité sans rien recoder).
 */
(function () {
    "use strict";

    let visionneuse = null;

    function creerVisionneuse() {
        visionneuse = document.createElement("dialog");
        visionneuse.className = "visionneuse";
        visionneuse.innerHTML =
            '<button type="button" class="visionneuse-fermer" aria-label="Fermer">×</button>' +
            '<img class="visionneuse-image" alt="">';
        // Un clic n'importe où (fond, image, bouton) referme : simple à comprendre
        visionneuse.addEventListener("click", () => visionneuse.close());
        // On vide l'image à la fermeture : la prochaine ne montre pas l'ancienne
        visionneuse.addEventListener("close", () => {
            visionneuse.querySelector("img").removeAttribute("src");
        });
        document.body.appendChild(visionneuse);
    }

    document.addEventListener("click", (evenement) => {
        const lien = evenement.target.closest("a[data-agrandir]");
        if (!lien || typeof HTMLDialogElement === "undefined") return; // vieux navigateur : le lien normal
        evenement.preventDefault();
        if (!visionneuse) creerVisionneuse();
        const image = visionneuse.querySelector("img");
        image.src = lien.href;
        image.alt = lien.querySelector("img")?.alt || "";
        visionneuse.showModal();
    });
})();
