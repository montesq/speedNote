from app import types_devoir


def test_type_valide_accepte_type_connu():
    assert types_devoir.type_valide("Oral") == "Oral"


def test_type_valide_replie_sur_premier_type_si_invalide():
    assert types_devoir.type_valide("Bidule") == types_devoir.TYPES[0]


def test_sous_type_valide_pour_type_qui_supporte_les_sous_types():
    assert types_devoir.sous_type_valide("Commentaire", "Introduction") == "Introduction"
    assert types_devoir.sous_type_valide("Dissertation", "Conclusion") == "Conclusion"


def test_sous_type_invalide_est_rejete():
    assert types_devoir.sous_type_valide("Commentaire", "Bidule") is None


def test_sous_type_toujours_none_pour_type_qui_ne_le_supporte_pas():
    assert types_devoir.sous_type_valide("Oral", "Introduction") is None
