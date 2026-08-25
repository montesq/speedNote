"""Génération des rapports PDF individuels (un par élève) pour un devoir,
au format A5 (une demi-page A4).

La mise en page (en-tête + note) est volontairement compacte pour laisser
un maximum de place à l'appréciation, et la taille de police de
l'appréciation s'ajuste automatiquement (11pt → 7pt) pour garantir qu'un
texte de plusieurs centaines de caractères tienne sur une seule page, sans
jamais déborder sur une seconde feuille."""

import re
import unicodedata
from pathlib import Path

from fpdf import FPDF

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
MARGE = 15

TEXTE = (45, 42, 58)
MUTED = (139, 133, 152)
BONNE = (13, 138, 95)
MOYENNE = (165, 114, 11)
FAIBLE = (194, 40, 54)
LIGNE = (230, 228, 220)

# Tailles de police candidates pour l'appréciation, de la plus lisible à la
# plus compacte — on prend la plus grande qui tient dans l'espace restant.
TAILLES_APPRECIATION = (11, 10, 9, 8, 7)


def slugifier(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = re.sub(r"[^a-zA-Z0-9]+", "-", texte).strip("-").lower()
    return texte or "rapport"


def _rendre_appreciation(pdf: FPDF, texte: str) -> None:
    """Affiche l'appréciation en choisissant la plus grande taille de police
    (parmi TAILLES_APPRECIATION) qui tient sur le reste de la page."""
    hauteur_disponible = (pdf.h - MARGE) - pdf.get_y()
    largeur = pdf.epw

    for taille in TAILLES_APPRECIATION:
        interligne = round(taille * 0.6, 2)
        pdf.set_font("DejaVu", "", taille)
        lignes = pdf.multi_cell(largeur, interligne, texte, align="L", split_only=True)
        if len(lignes) * interligne <= hauteur_disponible:
            break
    else:
        # Texte exceptionnellement long : dernier recours à la taille la
        # plus compacte (peut légèrement déborder dans des cas extrêmes).
        taille = TAILLES_APPRECIATION[-1]
        interligne = round(taille * 0.6, 2)

    pdf.set_font("DejaVu", "", taille)
    pdf.multi_cell(largeur, interligne, texte, align="L")


def generer_rapports(devoir, classe, lignes) -> bytes:
    """lignes : élève (nom, prenom), valeur, appreciation — une page A5 par élève."""
    pdf = FPDF(orientation="P", unit="mm", format="A5")
    pdf.set_auto_page_break(auto=True, margin=MARGE)
    pdf.add_font("DejaVu", "", str(FONTS_DIR / "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", str(FONTS_DIR / "DejaVuSans-Bold.ttf"))

    for ligne in lignes:
        pdf.add_page()
        pdf.set_margins(MARGE, MARGE, MARGE)

        pdf.set_font("DejaVu", "B", 17)
        pdf.set_text_color(*TEXTE)
        pdf.cell(0, 8, f"{ligne['prenom']} {ligne['nom']}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5.5, classe["nom"], new_x="LMARGIN", new_y="NEXT")

        pdf.ln(2.5)
        pdf.set_draw_color(*LIGNE)
        pdf.line(MARGE, pdf.get_y(), pdf.w - MARGE, pdf.get_y())
        pdf.ln(4)

        pdf.set_font("DejaVu", "B", 12)
        pdf.set_text_color(*TEXTE)
        pdf.multi_cell(pdf.epw, 6, devoir["titre"], align="L", new_x="LMARGIN", new_y="NEXT")

        if devoir["date_devoir"]:
            pdf.set_font("DejaVu", "", 9)
            pdf.set_text_color(*MUTED)
            pdf.cell(0, 5, devoir["date_devoir"], new_x="LMARGIN", new_y="NEXT")

        pdf.ln(3)

        valeur = ligne["valeur"]
        if valeur is not None:
            note_texte = f"{valeur:g} / 20"
            ratio = valeur / 20
            if ratio >= 0.7:
                pdf.set_text_color(*BONNE)
            elif ratio >= 0.5:
                pdf.set_text_color(*MOYENNE)
            else:
                pdf.set_text_color(*FAIBLE)
        else:
            note_texte = "Non noté"
            pdf.set_text_color(*MUTED)
        pdf.set_font("DejaVu", "B", 20)
        pdf.cell(0, 11, note_texte, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(3)
        pdf.set_text_color(*TEXTE)
        appreciation = ligne["appreciation"] or "Aucune appréciation."
        _rendre_appreciation(pdf, appreciation)

    return bytes(pdf.output())
