"""
Construit le rapport de certification à partir du template de l'école :
garde la couverture, le sommaire, les en-têtes/pieds et les styles ; remplace
le corps par le contenu de contenu_rapport.py ; ajoute les images.
Usage : python construire_rapport.py <template_dir> <sortie.docx>
"""
import os
import re
import shutil
import sys
import zipfile
from xml.sax.saxutils import escape

from PIL import Image as PILImage

sys.path.insert(0, os.path.dirname(__file__))
from contenu_rapport import CONTENU, CAPTURES, COUVERTURE  # noqa: E402

TEMPLATE, SORTIE = sys.argv[1], sys.argv[2]
DOSSIER_CAPTURES = os.path.join(os.path.dirname(SORTIE), "captures")

POLICE = '<w:rFonts w:ascii="Nunito Sans" w:cs="Nunito Sans" w:eastAsia="Nunito Sans" w:hAnsi="Nunito Sans"/>'
CODE = '<w:rFonts w:ascii="Consolas" w:cs="Consolas" w:eastAsia="Consolas" w:hAnsi="Consolas"/>'

images = []  # (rId, nom de fichier dans word/media, chemin source)
compteur = {"doc": 100}


def runs(texte, base_rpr=""):
    """Petit balisage : **gras**, `code`, _italique_ (entre soulignés simples)."""
    # Espaces insécables dans les guillemets : sinon Word peut laisser « seul en fin de ligne
    texte = texte.replace("« ", "« ").replace(" »", " »")
    morceaux = re.split(r"(\*\*[^*]+\*\*|`[^`]+`|(?<![\w])_[^_]+_(?![\w]))", texte)
    xml = []
    for m in morceaux:
        if not m:
            continue
        rpr = POLICE + '<w:color w:val="222222"/>' + base_rpr
        if m.startswith("**"):
            m, rpr = m[2:-2], rpr + "<w:b/>"
        elif m.startswith("`"):
            m, rpr = m[1:-1], CODE + '<w:color w:val="7A1C1C"/><w:sz w:val="19"/>'
        elif m.startswith("_") and m.endswith("_") and len(m) > 2:
            m, rpr = m[1:-1], rpr + "<w:i/>"
        xml.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(m)}</w:t></w:r>')
    return "".join(xml)


def para(texte, ppr="", rpr=""):
    return (f'<w:p><w:pPr>{ppr}<w:spacing w:before="80" w:after="120" w:line="276" w:lineRule="auto"/>'
            f'<w:jc w:val="both"/></w:pPr>{runs(texte, rpr)}</w:p>')


def titre(texte, niveau, saut=False):
    pb = '<w:pageBreakBefore/>' if saut else ''
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading{niveau}"/>{pb}<w:keepNext/></w:pPr>'
            f'<w:r><w:rPr>{POLICE}</w:rPr><w:t xml:space="preserve">{escape(texte)}</w:t></w:r></w:p>')


def puce(texte):
    return (f'<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="12"/></w:numPr>'
            f'<w:spacing w:before="0" w:after="60" w:line="264" w:lineRule="auto"/>'
            f'<w:ind w:left="720" w:hanging="360"/><w:jc w:val="both"/></w:pPr>{runs(texte)}</w:p>')


def code(lignes):
    xml = []
    for i, ligne in enumerate(lignes):
        avant = 120 if i == 0 else 0
        apres = 120 if i == len(lignes) - 1 else 0
        xml.append(
            f'<w:p><w:pPr><w:keepLines/>{"<w:keepNext/>" if i < len(lignes) - 1 else ""}'
            f'<w:shd w:val="clear" w:color="auto" w:fill="F3EFE6"/>'
            f'<w:spacing w:before="{avant}" w:after="{apres}" w:line="240" w:lineRule="auto"/>'
            f'<w:ind w:left="284" w:right="284"/></w:pPr>'
            f'<w:r><w:rPr>{CODE}<w:color w:val="2A1B10"/><w:sz w:val="17"/></w:rPr>'
            f'<w:t xml:space="preserve">{escape(ligne) or " "}</w:t></w:r></w:p>')
    return "".join(xml)


def a_inserer(texte):
    """Emplacement à compléter par Quentin : surligné en jaune, impossible à rater."""
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="120"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr>{POLICE}<w:b/><w:highlight w:val="yellow"/></w:rPr>'
            f'<w:t xml:space="preserve">[À COMPLÉTER] {escape(texte)}</w:t></w:r></w:p>')


def legende(texte):
    return (f'<w:p><w:pPr><w:spacing w:before="40" w:after="200"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr>{POLICE}<w:i/><w:color w:val="666666"/><w:sz w:val="18"/></w:rPr>'
            f'<w:t xml:space="preserve">{escape(texte)}</w:t></w:r></w:p>')


def drawing(chemin, largeur_cm):
    rid = f"rIdImg{len(images) + 1}"
    ext = os.path.splitext(chemin)[1].lower().replace(".jpeg", ".jpg")
    nom = f"capture{len(images) + 1}{ext}"
    images.append((rid, nom, chemin))
    with PILImage.open(chemin) as im:
        w, h = im.size
    cx = int(largeur_cm * 360000)
    cy = int(cx * h / w)
    compteur["doc"] += 1
    n = compteur["doc"]
    return (f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:docPr id="{n}" name="Image {n}"/>'
            f'<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{n}" name="{nom}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:ln w="6350"><a:solidFill><a:srgbClr val="BFBFBF"/></a:solidFill></a:ln></pic:spPr>'
            f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>')


def image(cle, largeur_cm, texte_legende):
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="0"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r>{drawing(CAPTURES[cle], largeur_cm)}</w:r></w:p>' + legende(texte_legende))


def cellule(contenu_xml, largeur, fond=None):
    shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fond}"/>' if fond else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{largeur}" w:type="dxa"/>{shd}'
            f'<w:tcMar><w:top w:w="60" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/></w:tcMar>'
            f'<w:vAlign w:val="center"/></w:tcPr>{contenu_xml}</w:tc>')


def tableau(lignes, largeurs, entete=True):
    total = sum(largeurs)
    grille = "".join(f'<w:gridCol w:w="{l}"/>' for l in largeurs)
    bord = '<w:{0} w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
    bords = "".join(bord.format(c) for c in ("top", "left", "bottom", "right", "insideH", "insideV"))
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/>'
           f'<w:tblBorders>{bords}</w:tblBorders><w:tblLayout w:type="fixed"/>'
           f'<w:tblCellMar><w:left w:w="100" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>'
           f'</w:tblPr><w:tblGrid>{grille}</w:tblGrid>']
    for i, ligne in enumerate(lignes):
        est_entete = entete and i == 0
        xml.append('<w:tr>' + ('<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' if est_entete else '<w:trPr><w:cantSplit/></w:trPr>'))
        for texte, largeur in zip(ligne, largeurs):
            rpr = '<w:b/>' if est_entete else ''
            p = (f'<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="252" w:lineRule="auto"/></w:pPr>'
                 f'{runs(texte, rpr + "<w:sz w:val=\"19\"/>")}</w:p>')
            xml.append(cellule(p, largeur, "EFE7D6" if est_entete else None))
        xml.append('</w:tr>')
    xml.append('</w:tbl>')
    return "".join(xml) + '<w:p><w:pPr><w:spacing w:before="0" w:after="120"/></w:pPr></w:p>'


def deux_images(cle1, cle2, largeur_cm, texte_legende):
    """Deux captures côte à côte (téléphone) dans un tableau sans bordure."""
    larg = 4800
    cell = lambda cle: (f'<w:tc><w:tcPr><w:tcW w:w="{larg}" w:type="dxa"/></w:tcPr>'
                        f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r>{drawing(CAPTURES[cle], largeur_cm)}</w:r></w:p></w:tc>')
    sans = "".join(f'<w:{c} w:val="nil"/>' for c in ("top", "left", "bottom", "right", "insideH", "insideV"))
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{2 * larg}" w:type="dxa"/><w:jc w:val="center"/>'
            f'<w:tblBorders>{sans}</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{larg}"/><w:gridCol w:w="{larg}"/></w:tblGrid>'
            f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{cell(cle1)}{cell(cle2)}</w:tr></w:tbl>') + legende(texte_legende)


def cadrage(chemin):
    """Annexe 1 : le texte du document de cadrage, repris paragraphe par paragraphe."""
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    from xml.etree import ElementTree as ET
    racine = ET.fromstring(zipfile.ZipFile(chemin).read("word/document.xml"))
    xml = []
    for p in racine.find(W + "body").iter(W + "p"):
        texte = "".join(t.text or "" for t in p.iter(W + "t")).strip()
        if not texte:
            continue
        style = p.find(f"{W}pPr/{W}pStyle")
        style = style.get(W + "val") if style is not None else ""
        if texte.startswith("SECTION") or texte.startswith("DOCUMENT DE CADRAGE"):
            xml.append(titre(texte.capitalize() if texte.isupper() else texte, 3))
        elif style.startswith("ListBullet"):
            xml.append(puce(texte.lstrip("• ")))
        elif re.match(r"^\d\. ", texte):
            xml.append(para("**" + texte + "**"))
        else:
            xml.append(para(texte))
    return "".join(xml)


RENDU = {
    "cadrage": cadrage,
    "h1": lambda t: titre(t, 1, saut=True),
    "h1s": lambda t: titre(t, 1),
    "h2": lambda t: titre(t, 2),
    "h3": lambda t: titre(t, 3),
    "p": para,
    "li": puce,
    "code": code,
    "todo": a_inserer,
    "img": lambda a: image(*a),
    "img2": lambda a: deux_images(*a),
    "table": lambda a: tableau(*a),
}

# ------------------------------------------------------------------ assemblage
doc = open(os.path.join(TEMPLATE, "word", "document.xml"), encoding="utf-8").read()
debut_corps = doc.index("<w:body>") + len("<w:body>")
fin_corps = doc.index("<w:sectPr", doc.rindex("</w:p>"))
corps = doc[debut_corps:fin_corps]

# Découpe en éléments de premier niveau (p, tbl, sdt)
elements, pos, profondeur, debut = [], 0, 0, None
for m in re.finditer(r"<(/?)w:(p|tbl|sdt)\b[^>]*?(/?)>", corps):
    fermeture, autofermante = m.group(1) == "/", m.group(3) == "/"
    if not fermeture:
        if profondeur == 0:
            debut = m.start()
        if autofermante:
            if profondeur == 0:
                elements.append(corps[debut:m.end()])
            continue
        profondeur += 1
    else:
        profondeur -= 1
        if profondeur == 0:
            elements.append(corps[debut:m.end()])
assert len(elements) == 88, len(elements)


def remplacer_texte(xml, nouveau):
    """Met `nouveau` dans le premier <w:t>, vide les autres (les runs de Word sont éclatés)."""
    vus = {"n": 0}

    def sub(m):
        vus["n"] += 1
        return f'{m.group(1)}{escape(nouveau) if vus["n"] == 1 else ""}</w:t>'
    return re.sub(r"(<w:t(?: [^>]*)?>)[^<]*</w:t>", sub, xml)


couverture = elements[:13] + elements[14:20] + elements[21:25]  # sans le tableau « Remarques », un seul auteur
couverture[4] = remplacer_texte(couverture[4], COUVERTURE["titre"])
couverture[10] = remplacer_texte(couverture[10], COUVERTURE["date"])
couverture[18] = remplacer_texte(couverture[18], COUVERTURE["auteur"])
# Le sommaire sur sa propre page (la couverture reste seule) ; deux niveaux seulement
couverture[21] = couverture[21].replace("<w:pPr>", "<w:pPr><w:pageBreakBefore/>", 1)
_debut = couverture[22].index("TOC "); _fin = couverture[22].index("&quot;", couverture[22].index("&quot;", _debut) + 6) + 6
couverture[22] = couverture[22][:_debut] + r"TOC \h \u \z \o &quot;1-2&quot;" + couverture[22][_fin:]

nouveau_corps = "".join(couverture) + "".join(RENDU[cle](val) for cle, val in CONTENU)
doc = doc[:debut_corps] + nouveau_corps + doc[fin_corps:]
# Espaces de noms nécessaires aux images (déjà déclarés dans le template ?)
for prefixe, uri in (("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"),
                     ("a", "http://schemas.openxmlformats.org/drawingml/2006/main"),
                     ("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture"),
                     ("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")):
    if f"xmlns:{prefixe}=" not in doc[:3000]:
        doc = doc.replace("<w:document ", f'<w:document xmlns:{prefixe}="{uri}" ', 1)

# ------------------------------------------------------------------ écriture
travail = SORTIE + ".dossier"
if os.path.exists(travail):
    shutil.rmtree(travail)
shutil.copytree(TEMPLATE, travail)
open(os.path.join(travail, "word", "document.xml"), "w", encoding="utf-8").write(doc)

rels_chemin = os.path.join(travail, "word", "_rels", "document.xml.rels")
rels = open(rels_chemin, encoding="utf-8").read()
ajout = "".join(
    f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{nom}"/>'
    for rid, nom, _ in images)
open(rels_chemin, "w", encoding="utf-8").write(rels.replace("</Relationships>", ajout + "</Relationships>"))
os.makedirs(os.path.join(travail, "word", "media"), exist_ok=True)
for _, nom, chemin in images:
    shutil.copy(chemin, os.path.join(travail, "word", "media", nom))

ct_chemin = os.path.join(travail, "[Content_Types].xml")
ct = open(ct_chemin, encoding="utf-8").read()
if 'Extension="jpg"' not in ct:
    ct = ct.replace("<Default ", '<Default ContentType="image/jpeg" Extension="jpg"/><Default ', 1)
open(ct_chemin, "w", encoding="utf-8").write(ct)

# Word met le sommaire à jour à l'ouverture (il propose de mettre à jour les champs)
reglages_chemin = os.path.join(travail, "word", "settings.xml")
reglages = open(reglages_chemin, encoding="utf-8").read()
if "w:updateFields" not in reglages:
    reglages = re.sub(r"(<w:settings[^>]*>)", r'\1<w:updateFields w:val="true"/>', reglages, count=1)
open(reglages_chemin, "w", encoding="utf-8").write(reglages)

if os.path.exists(SORTIE):
    os.remove(SORTIE)
with zipfile.ZipFile(SORTIE, "w", zipfile.ZIP_DEFLATED) as z:
    for racine, _, fichiers in os.walk(travail):
        for f in fichiers:
            complet = os.path.join(racine, f)
            z.write(complet, os.path.relpath(complet, travail).replace(os.sep, "/"))
shutil.rmtree(travail)

# Les captures, rangées à côté du rapport (utiles pour l'oral)
os.makedirs(DOSSIER_CAPTURES, exist_ok=True)
for cle, chemin in CAPTURES.items():
    cible = os.path.join(DOSSIER_CAPTURES, cle + os.path.splitext(chemin)[1])
    if os.path.abspath(chemin) != os.path.abspath(cible):
        shutil.copy(chemin, cible)
print(f"{SORTIE} : {len(CONTENU)} blocs, {len(images)} images")
