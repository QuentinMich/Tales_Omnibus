/*
 * ÉDITEUR DE CARTE (admin Wagtail, page Carte)
 *
 * Deux morceaux côté HTML :
 *   - [data-editeur-carte] : l'image de la carte, en grand (EditeurDeCartePanel) ;
 *   - [data-outils-carte] : sur CHAQUE lieu de « Lieux sur cette carte »,
 *     le champ caché « forme » et les boutons Placer / Tracer / Effacer.
 *
 * Principe : un bouton choisit la LIGNE active (le lieu qu'on édite) et le
 * MODE (point ou zone). Ensuite, les clics sur l'image remplissent les
 * champs de cette ligne : coord_x / coord_y pour un point, la liste des
 * sommets (JSON) dans « forme » pour une zone. Toutes les valeurs sont en %
 * de l'image, comme sur le site : 0 = bord gauche/haut, 100 = bord droit/bas.
 *
 * Le calcul « qui est dans qui » ne se fait PAS ici mais en Python, à la
 * publication (CartePage.ranger_les_lieux) : une seule source de vérité.
 */
(function () {
    "use strict";

    let editeur, cadre, image, calqueZones, calquePoints, barre, statut;
    let ligneActive = null; // { input, prefixe, element } du lieu en cours d'édition
    let mode = null;        // "point", "zone" ou null (rien en cours)
    let sommets = [];       // la zone en cours de tracé : [[x, y], ...]

    const SVG = "http://www.w3.org/2000/svg";
    const arrondi = (n) => Math.round(n * 100) / 100;

    /* ---------- Lire / écrire les champs d'une ligne ---------- */

    // Toutes les lignes « lieu » encore présentes (pas supprimées)
    function lignes() {
        return Array.from(document.querySelectorAll("[data-outils-carte] input[type=hidden]"))
            .map(ligneDe)
            .filter((ligne) => !ligne.supprimee);
    }

    // Les noms des champs d'une ligne : "apparitions-3-forme" -> préfixe "apparitions-3-"
    function ligneDe(input) {
        const prefixe = input.name.slice(0, -"forme".length);
        const champ = (nom) => document.querySelector(`[name="${prefixe}${nom}"]`);
        const element = input.closest("[data-inline-panel-child], li") || input.parentElement;
        const supprime = champ("DELETE");
        return {
            input,
            prefixe,
            element,
            x: champ("coord_x"),
            y: champ("coord_y"),
            manuel: champ("centre_manuel"), // case « Centre placé à la main »
            motif: champ("motif"),          // remplissage : pleine / hachurée
            bordure: champ("bordure"),      // frontière : continue / tirets
            supprimee: !!supprime && (supprime.value === "1" || supprime.checked === true),
        };
    }

    function forme(ligne) {
        try {
            const valeur = JSON.parse(ligne.input.value || "null");
            return Array.isArray(valeur) && valeur.length >= 3 ? valeur : null;
        } catch (e) {
            return null;
        }
    }

    function point(ligne) {
        const x = parseFloat(String(ligne.x?.value).replace(",", "."));
        const y = parseFloat(String(ligne.y?.value).replace(",", "."));
        return Number.isFinite(x) && Number.isFinite(y) ? [x, y] : null;
    }

    // Le nom du lieu, lu dans le sélecteur de page de la ligne
    function nom(ligne) {
        const titre = ligne.element.querySelector("[data-chooser-title], .chooser__title");
        return (titre && titre.textContent.trim()) || "Lieu à choisir";
    }

    function ecrire(champ, valeur) {
        if (!champ) return;
        champ.value = valeur;
        // Prévient Wagtail que le formulaire a changé (alerte « modifications non enregistrées »)
        champ.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function centreManuel(ligne) {
        return !!(ligne.manuel && ligne.manuel.checked);
    }

    function cocherManuel(ligne, valeur) {
        if (!ligne.manuel) return;
        ligne.manuel.checked = valeur;
        ligne.manuel.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function ecrirePoint(ligne, x, y) {
        ecrire(ligne.x, x === "" ? "" : arrondi(x));
        ecrire(ligne.y, y === "" ? "" : arrondi(y));
    }

    /* ---------- Géométrie (la même formule que geometrie.centre en Python) ---------- */

    function centre(poly) {
        let a = 0, cx = 0, cy = 0;
        poly.forEach(([x1, y1], i) => {
            const [x2, y2] = poly[(i + 1) % poly.length];
            const croix = x1 * y2 - x2 * y1;
            a += croix;
            cx += (x1 + x2) * croix;
            cy += (y1 + y2) * croix;
        });
        if (Math.abs(a) < 1e-9) {
            return [poly.reduce((s, p) => s + p[0], 0) / poly.length, poly.reduce((s, p) => s + p[1], 0) / poly.length];
        }
        a /= 2;
        return [cx / (6 * a), cy / (6 * a)];
    }

    // Point dans un polygone : l'algorithme du rayon, comme geometrie.contient en Python
    function dansLaZone(poly, x, y) {
        let dedans = false;
        poly.forEach(([x1, y1], i) => {
            const [x2, y2] = poly[(i + 1) % poly.length];
            if ((y1 > y) !== (y2 > y) && x < x1 + ((y - y1) * (x2 - x1)) / (y2 - y1)) dedans = !dedans;
        });
        return dedans;
    }

    /* ---------- Dessin ---------- */

    function element(nomBalise, attributs, parent, ns) {
        const el = ns ? document.createElementNS(SVG, nomBalise) : document.createElement(nomBalise);
        Object.entries(attributs).forEach(([cle, valeur]) => el.setAttribute(cle, valeur));
        parent.appendChild(el);
        return el;
    }

    function dessiner() {
        if (!editeur) return;
        calqueZones.replaceChildren();
        calquePoints.replaceChildren();

        lignes().forEach((ligne) => {
            const active = ligneActive && ligneActive.input === ligne.input;
            const zone = forme(ligne);
            // Le repère d'une zone : son centre placé à la main, sinon calculé
            const pt = zone ? (centreManuel(ligne) && point(ligne)) || centre(zone) : point(ligne);
            const classe = active ? " est-active" : "";

            if (zone) {
                // Aperçu du remplissage et de la frontière choisis dans les menus de la ligne
                const style = (ligne.motif?.value === "hachures" ? " est-hachuree" : "")
                    + (ligne.bordure?.value === "tirets" ? " est-en-tirets" : "");
                element("polygon", { points: zone.map((p) => p.join(",")).join(" "), class: "editeur-carte__zone" + style + classe }, calqueZones, true);
            }
            if (pt) {
                const repere = element("span", { class: (zone ? "editeur-carte__nom" : "editeur-carte__point") + classe }, calquePoints);
                repere.style.left = pt[0] + "%";
                repere.style.top = pt[1] + "%";
                repere.textContent = nom(ligne);
            }

            // Le petit résumé à côté des boutons de la ligne
            const resume = ligne.input.closest("[data-outils-carte]").querySelector("[data-resume]");
            if (resume) {
                resume.textContent = zone
                    ? `Zone de ${zone.length} coins`
                    : pt ? `Point en ${arrondi(pt[0])} %, ${arrondi(pt[1])} %` : "Pas encore placé";
            }
            ligne.element.classList.toggle("est-en-edition", !!active);
        });

        // La zone en cours de tracé : une ligne brisée + un rond par coin
        if (mode === "zone" && sommets.length) {
            element("polyline", { points: sommets.map((p) => p.join(",")).join(" "), class: "editeur-carte__trace" }, calqueZones, true);
            sommets.forEach(([x, y], i) => {
                const coin = element("span", { class: "editeur-carte__coin" + (i === 0 ? " est-premier" : "") }, calquePoints);
                coin.style.left = x + "%";
                coin.style.top = y + "%";
            });
        }
    }

    /* ---------- Modes ---------- */

    function demarrer(ligne, nouveauMode) {
        if (cadre.hidden) {
            alert("Choisis d'abord l'image de la carte (et attends qu'elle s'affiche).");
            return;
        }
        if (nouveauMode === "centre" && !forme(ligne)) {
            alert("Trace d'abord la zone : le centre se place à l'intérieur.");
            return;
        }
        ligneActive = ligne;
        mode = nouveauMode;
        sommets = [];
        barre.hidden = false;
        barre.querySelector("[data-action=terminer]").hidden = mode !== "zone";
        cadre.classList.add("est-en-mode");
        statut.textContent = {
            point: `« ${nom(ligne)} » : clique sur la carte pour le placer.`,
            zone: `« ${nom(ligne)} » : un clic par coin. Double-clic (ou clic sur le premier coin) pour fermer.`,
            centre: `« ${nom(ligne)} » : clique DANS la zone, là où son nom doit s'afficher.`,
        }[mode];
        dessiner();
        editeur.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function finir() {
        const ligne = ligneActive;
        ligneActive = null;
        mode = null;
        sommets = [];
        barre.hidden = true;
        cadre.classList.remove("est-en-mode");
        dessiner();
        // On revient au lieu qu'on vient de placer
        if (ligne) ligne.element.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function terminerZone() {
        if (mode !== "zone") return;
        if (sommets.length < 3) {
            statut.textContent = "Il faut au moins 3 coins pour faire une zone.";
            return;
        }
        const zone = sommets.map(([x, y]) => [arrondi(x), arrondi(y)]);
        ecrire(ligneActive.input, JSON.stringify(zone));
        // L'étoile d'une zone = son centre (le Python fera pareil à la publication)
        const [x, y] = centre(zone);
        ecrirePoint(ligneActive, x, y);
        cocherManuel(ligneActive, false); // nouvelle forme = centre recalculé
        finir();
    }

    /* ---------- Clics ---------- */

    // Position du clic en % de l'image
    function position(evenement) {
        const r = image.getBoundingClientRect();
        const borne = (v) => Math.min(100, Math.max(0, v));
        return [borne(((evenement.clientX - r.left) / r.width) * 100), borne(((evenement.clientY - r.top) / r.height) * 100)];
    }

    function clicSurLaCarte(evenement) {
        if (!mode) return;
        // detail = numéro du clic : le 2e clic d'un double-clic n'ajoute pas de coin
        if (evenement.detail > 1) return;
        const [x, y] = position(evenement);

        if (mode === "point") {
            ecrire(ligneActive.input, ""); // un point n'a pas de zone
            ecrirePoint(ligneActive, x, y);
            cocherManuel(ligneActive, false);
            finir();
            return;
        }
        if (mode === "centre") {
            if (!dansLaZone(forme(ligneActive), x, y)) {
                statut.textContent = "Raté : le centre doit être à l'intérieur de la zone. Réessaie !";
                return;
            }
            ecrirePoint(ligneActive, x, y);
            cocherManuel(ligneActive, true);
            finir();
            return;
        }
        // Mode zone : clic près du premier coin = on ferme la forme
        if (sommets.length >= 3) {
            const [px, py] = sommets[0];
            if (Math.hypot(px - x, py - y) < 2) {
                terminerZone();
                return;
            }
        }
        sommets.push([x, y]);
        statut.textContent = `${sommets.length} coin(s) posé(s). Double-clic ou clic sur le premier coin pour fermer.`;
        dessiner();
    }

    function clicSurUnBouton(evenement) {
        const bouton = evenement.target.closest("[data-outil], [data-action]");
        if (!bouton || !editeur) return;

        if (bouton.dataset.action === "terminer") return terminerZone();
        if (bouton.dataset.action === "annuler") return finir();

        const ligne = ligneDe(bouton.closest("[data-outils-carte]").querySelector("input[type=hidden]"));
        if (bouton.dataset.outil === "effacer") {
            ecrire(ligne.input, "");
            ecrirePoint(ligne, "", "");
            cocherManuel(ligne, false);
            if (ligneActive && ligneActive.input === ligne.input) finir();
            dessiner();
        } else {
            demarrer(ligne, bouton.dataset.outil);
        }
    }

    function clavier(evenement) {
        if (!mode) return;
        if (evenement.key === "Escape") finir();
        if (evenement.key === "Enter" && mode === "zone") {
            evenement.preventDefault(); // sinon Entrée enverrait le formulaire
            terminerZone();
        }
        if (evenement.key === "Backspace" && mode === "zone" && sommets.length && !evenement.target.matches("input, textarea")) {
            evenement.preventDefault();
            sommets.pop(); // retire le dernier coin
            dessiner();
        }
    }

    /* ---------- L'image de la carte ---------- */

    // L'image choisie dans le formulaire (champ main_image). On la surveille :
    // si on en choisit une autre, l'éditeur se met à jour sans recharger.
    let imageAffichee = null;
    function suivreImage() {
        const champ = document.querySelector("input[name=main_image]");
        const id = champ ? champ.value : "";
        if (id === imageAffichee) return;
        imageAffichee = id;
        if (!id) {
            cadre.hidden = true;
            return;
        }
        const url = editeur.dataset.urlImage.replace(/0\/$/, id + "/");
        fetch(url, { credentials: "same-origin" })
            .then((reponse) => (reponse.ok ? reponse.json() : Promise.reject(reponse.status)))
            .then((donnees) => {
                image.src = donnees.url;
                cadre.hidden = false;
                dessiner();
            })
            .catch(() => { cadre.hidden = true; });
    }

    /* ---------- Démarrage ---------- */

    function demarrage() {
        editeur = document.querySelector("[data-editeur-carte]");
        if (!editeur) return;
        cadre = editeur.querySelector("[data-cadre]");
        image = editeur.querySelector("[data-image]");
        calqueZones = editeur.querySelector("[data-zones]");
        calquePoints = editeur.querySelector("[data-points]");
        barre = editeur.querySelector("[data-barre]");
        statut = editeur.querySelector("[data-statut]");

        cadre.addEventListener("click", clicSurLaCarte);
        cadre.addEventListener("dblclick", terminerZone);
        document.addEventListener("click", clicSurUnBouton);
        document.addEventListener("keydown", clavier);
        // Une coordonnée tapée à la main, un lieu choisi, une ligne supprimée… on redessine
        document.addEventListener("change", (e) => { if (e.target.name && e.target.name.startsWith("apparitions-")) dessiner(); });
        document.addEventListener("input", (e) => { if (e.target.name && /-coord_[xy]$/.test(e.target.name)) dessiner(); });

        // Une nouvelle ligne « Lieu » ajoutée : on redessine (pour son résumé)
        const liste = document.getElementById("id_apparitions-FORMS");
        if (liste) new MutationObserver(dessiner).observe(liste, { childList: true });

        suivreImage();
        setInterval(suivreImage, 1000); // le sélecteur d'image ne prévient pas toujours
        // Le nom d'un lieu n'est pas un champ : on rafraîchit de temps en temps
        setInterval(() => { if (!mode) dessiner(); }, 2000);
        dessiner();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", demarrage);
    } else {
        demarrage();
    }
})();
