from app import rapports


def test_slugifier_normalise_accents_et_espaces():
    assert rapports.slugifier("Épreuve d'invention !") == "epreuve-d-invention"


def test_slugifier_texte_vide_a_un_repli():
    assert rapports.slugifier("") == "rapport"
    assert rapports.slugifier("!!!") == "rapport"


def test_generer_rapports_produit_un_pdf_valide():
    devoir = {"titre": "Dissertation", "date_devoir": "2026-01-14"}
    classe = {"nom": "1re B"}
    lignes = [
        {"nom": "Dupuis", "prenom": "Léa", "valeur": 15.0, "appreciation": "Bon travail."},
        {"nom": "Martin", "prenom": "Lucas", "valeur": None, "appreciation": None},
    ]
    pdf_bytes = rapports.generer_rapports(devoir, classe, lignes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_generer_rapports_gere_appreciation_longue_sans_deborder():
    devoir = {"titre": "Devoir", "date_devoir": None}
    classe = {"nom": "Classe"}
    appreciation_longue = "Analyse détaillée. " * 60  # ~1140 caractères
    lignes = [{"nom": "Test", "prenom": "Élève", "valeur": 12.0, "appreciation": appreciation_longue}]
    pdf_bytes = rapports.generer_rapports(devoir, classe, lignes)
    assert pdf_bytes.startswith(b"%PDF")
