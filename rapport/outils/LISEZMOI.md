# Régénérer le rapport

Le texte du rapport est dans `contenu_rapport.py` (balisage : `**gras**`,
`` `code` ``, `_italique_` ; blocs `h1`, `h2`, `h3`, `p`, `li`, `table`, `code`,
`img`, `img2`, `todo` = surligné en jaune « [À COMPLÉTER] »).
`template/` est le template de l'école, décompressé (couverture, sommaire,
en-têtes, styles). Les images viennent de `../captures/`.

Depuis ce dossier (`rapport/outils`), sous Windows :

```bash
../../env/Scripts/python.exe construire_rapport.py template ../Rapport_Tales_Omnibus.docx
```

```bash
powershell -ExecutionPolicy Bypass -File word_pdf.ps1 "<chemin absolu>\Rapport_Tales_Omnibus.docx" "<chemin absolu>\Rapport_Tales_Omnibus.pdf"
```

`word_pdf.ps1` passe par Word (il met aussi le sommaire à jour) ;
`pdf_png.ps1 <pdf> <dossier>` rend chaque page en PNG pour vérifier la mise
en page. Le corps (Résumé → Conclusion) doit tenir en **15 pages maximum**
(pages 3 à 17 actuellement : il n'y a plus de marge).

Fermer le .docx dans Word avant de régénérer, sinon le fichier est verrouillé.
