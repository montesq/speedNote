"""Tests du bilan de synthèse IA. Le modèle de langage local (Llama, ~770 Mo,
plusieurs dizaines de secondes par génération) est toujours mocké ici — le
tester réellement se fait manuellement, pas dans la suite de non-régression."""

import json
from unittest.mock import MagicMock, patch

from app import bilan


def test_generer_bilan_sans_appreciation_ne_sollicite_pas_le_modele():
    with patch("app.bilan._get_llm") as get_llm:
        resultat = bilan.generer_bilan("Camille Dupuis", [])
    get_llm.assert_not_called()
    assert "Aucune appréciation" in resultat


def test_generer_bilan_ignore_les_commentaires_sans_appreciation():
    commentaires = [
        {"devoir_titre": "Devoir 1", "valeur": 12, "appreciation": ""},
        {"devoir_titre": "Devoir 2", "valeur": None, "appreciation": None},
    ]
    with patch("app.bilan._get_llm") as get_llm:
        resultat = bilan.generer_bilan("Camille Dupuis", commentaires)
    get_llm.assert_not_called()
    assert "Aucune appréciation" in resultat


def test_generer_bilan_appelle_le_modele_avec_le_contexte(monkeypatch):
    faux_llm = MagicMock()
    faux_llm.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "  Synthèse générée.  "}}]
    }
    monkeypatch.setattr(bilan, "_get_llm", lambda: faux_llm)

    commentaires = [{"devoir_titre": "Dissertation", "valeur": 14.0, "appreciation": "Bon travail."}]
    resultat = bilan.generer_bilan("Camille Dupuis", commentaires)

    assert resultat == "Synthèse générée."
    appel = faux_llm.create_chat_completion.call_args.kwargs
    messages = appel["messages"]
    assert messages[0]["role"] == "system"
    assert "Camille Dupuis" in messages[1]["content"]
    assert "Dissertation" in messages[1]["content"]
    assert "Bon travail." in messages[1]["content"]


def test_generer_bilan_leve_une_erreur_si_le_modele_echoue(monkeypatch):
    faux_llm = MagicMock()
    faux_llm.create_chat_completion.side_effect = RuntimeError("plantage")
    monkeypatch.setattr(bilan, "_get_llm", lambda: faux_llm)

    commentaires = [{"devoir_titre": "Devoir", "valeur": 10.0, "appreciation": "Correct."}]
    try:
        bilan.generer_bilan("Test", commentaires)
        assert False, "une BilanError aurait dû être levée"
    except bilan.BilanError:
        pass


def test_route_bilan_generer_sans_commentaires(unlocked_client):
    r = unlocked_client.post("/bilan/generer", data={"nom": "Test", "commentaires": "[]"})
    assert r.status_code == 200
    assert "Aucune appréciation" in r.get_json()["bilan"]


def test_route_bilan_generer_json_malforme_ne_plante_pas(unlocked_client):
    r = unlocked_client.post("/bilan/generer", data={"nom": "Test", "commentaires": "pas du json"})
    assert r.status_code == 200


def test_route_bilan_generer_succes(unlocked_client, monkeypatch):
    monkeypatch.setattr(bilan, "generer_bilan", lambda nom, commentaires: "Synthèse de test.")
    commentaires = json.dumps([{"devoir_titre": "Devoir", "valeur": 12, "appreciation": "Correct."}])
    r = unlocked_client.post("/bilan/generer", data={"nom": "Camille Dupuis", "commentaires": commentaires})
    assert r.status_code == 200
    assert r.get_json()["bilan"] == "Synthèse de test."


def test_route_bilan_generer_erreur_modele(unlocked_client, monkeypatch):
    def echoue(nom, commentaires):
        raise bilan.BilanError("Modèle introuvable.")

    monkeypatch.setattr(bilan, "generer_bilan", echoue)
    commentaires = json.dumps([{"devoir_titre": "Devoir", "valeur": 12, "appreciation": "Correct."}])
    r = unlocked_client.post("/bilan/generer", data={"nom": "Test", "commentaires": commentaires})
    assert r.status_code == 500
    assert "Modèle introuvable" in r.get_json()["erreur"]
