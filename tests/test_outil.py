"""Tests de l'outil de dictée générale (/outil)."""

import io
from unittest.mock import patch


def test_page_outil_accessible(unlocked_client):
    r = unlocked_client.get("/outil")
    assert r.status_code == 200
    assert "Dictée vocale" in r.data.decode()


def test_lien_outil_present_dans_la_navigation(unlocked_client):
    r = unlocked_client.get("/outil")
    assert 'href="/outil"' in r.data.decode()


def test_page_outil_protegee_si_verrouille(client):
    from app import store

    store.create_new("test1234")
    store.lock()
    r = client.get("/outil", follow_redirects=False)
    assert r.status_code == 302
    assert "/deverrouiller" in r.headers["Location"]


def test_transcrire_renvoie_le_texte_nettoye(unlocked_client):
    with patch("app.voice.transcribe", return_value="bonjour virgule bon travial point"):
        r = unlocked_client.post(
            "/outil/transcrire", data={"audio": (io.BytesIO(b"faux-audio"), "dictee.webm")}
        )
    assert r.status_code == 200
    assert r.get_json()["texte"] == "Bonjour, bon travail."


def test_transcrire_sans_audio(unlocked_client):
    r = unlocked_client.post("/outil/transcrire", data={})
    assert r.status_code == 400
    assert "erreur" in r.get_json()


def test_transcrire_rien_compris(unlocked_client):
    with patch("app.voice.transcribe", return_value=""):
        r = unlocked_client.post(
            "/outil/transcrire", data={"audio": (io.BytesIO(b"faux-audio"), "dictee.webm")}
        )
    assert r.status_code == 200
    assert "erreur" in r.get_json()


def test_transcrire_erreur_modele(unlocked_client):
    from app import voice

    with patch("app.voice.transcribe", side_effect=voice.TranscriptionError("modèle introuvable")):
        r = unlocked_client.post(
            "/outil/transcrire", data={"audio": (io.BytesIO(b"faux-audio"), "dictee.webm")}
        )
    assert r.status_code == 500
    assert "modèle introuvable" in r.get_json()["erreur"]
