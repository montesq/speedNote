"""Tests de la logique d'extraction du transcript vocal (app/voice.py).
Ne touche jamais Vosk/ffmpeg : uniquement le parsing texte, qui est la
partie testable sans microphone ni modèle."""

from app.voice import _capitaliser_phrases, _corriger_orthographe, _ponctuer, _retirer_insensible_accents, parser


class Eleve(dict):
    def __getitem__(self, k):
        return dict.get(self, k)


def eleve(nom, prenom):
    return Eleve(nom=nom, prenom=prenom)


def test_parser_extrait_eleve_note_appreciation():
    eleves = [eleve("Dupuis", "Camille")]
    resultat = parser("camille dupuis quatorze bon travail mais peut approfondir l analyse", eleves)
    assert resultat["eleve"]["nom"] == "Dupuis"
    assert resultat["valeur"] == 14.0
    assert "dupuis" not in resultat["appreciation"].lower()
    assert "camille" not in resultat["appreciation"].lower()


def test_parser_nom_non_accentue_retire_correctement():
    """Régression : Vosk transcrit souvent les noms sans accent (ex. "traore"
    pour "Traoré") — le retrait doit rester insensible aux accents pour ne
    pas laisser un résidu que le correcteur orthographique corromprait."""
    eleves = [eleve("Traoré", "Aya")]
    resultat = parser("aya traore seize excellent travail", eleves)
    assert resultat["eleve"]["nom"] == "Traoré"
    assert "traore" not in resultat["appreciation"].lower()
    assert "traire" not in resultat["appreciation"].lower()


def test_parser_note_decimale_virgule():
    resultat = parser("quinze virgule cinq", [])
    assert resultat["valeur"] == 15.5


def test_parser_aucun_eleve_reconnu():
    resultat = parser("bon travail dans l ensemble", [eleve("Martin", "Lucas")])
    assert resultat["eleve"] is None


def test_retirer_insensible_accents():
    assert _retirer_insensible_accents("bonjour aya traore comment", "Traoré") == "bonjour aya  comment"
    assert _retirer_insensible_accents("rien a voir ici", "") == "rien a voir ici"


def test_ponctuation_convertie_en_signes():
    texte = _ponctuer("bonjour virgule ça va point")
    assert texte == "bonjour, ça va."


def test_ponctuation_point_exclamation_et_interrogation():
    assert _ponctuer("bravo point d exclamation") == "bravo!"
    assert _ponctuer("ça va point d interrogation") == "ça va?"


def test_saut_de_ligne_vs_a_la_ligne():
    texte = _ponctuer("premiere ligne saut de ligne deuxieme partie a la ligne suite")
    assert texte == "premiere ligne\n\ndeuxieme partie\nsuite"


def test_capitalisation_apres_chaque_phrase():
    texte = _capitaliser_phrases("bonjour. ça va bien. et toi?")
    assert texte == "Bonjour. Ça va bien. Et toi?"


def test_correction_orthographe_corrige_fautes_evidentes():
    corrige = _corriger_orthographe("bon travial et bonne orthografe")
    assert "travail" in corrige
    assert "orthographe" in corrige


def test_correction_orthographe_ne_touche_pas_les_mots_courts_ou_corrects():
    corrige = _corriger_orthographe("le chat est noir")
    assert corrige == "le chat est noir"
