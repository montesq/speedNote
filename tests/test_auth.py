"""Tests du cycle démarrage / déverrouillage / verrouillage.

Note : app.routes.auth garde un compteur de tentatives échouées au niveau
du module (pas par session), pour ralentir le brute-force. Chaque test qui
en dépend le remet à zéro explicitement pour rester indépendant de l'ordre
d'exécution."""

from app import store
from app.routes import auth


def _reset_backoff(monkeypatch):
    monkeypatch.setattr(auth, "_failed_attempts", 0)
    monkeypatch.setattr(auth, "_last_failure", 0.0)


def test_demarrage_cree_et_deverrouille_la_base(client):
    assert not store.is_initialized()
    r = client.post(
        "/demarrage",
        data={"passphrase": "unmotdepasse", "passphrase_confirm": "unmotdepasse"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert store.is_initialized()
    assert store.is_unlocked()


def test_demarrage_refuse_mot_de_passe_trop_court(client):
    r = client.post(
        "/demarrage",
        data={"passphrase": "abc", "passphrase_confirm": "abc"},
        follow_redirects=True,
    )
    assert "8 caractères" in r.data.decode()
    assert not store.is_initialized()


def test_demarrage_refuse_mots_de_passe_differents(client):
    r = client.post(
        "/demarrage",
        data={"passphrase": "unmotdepasse", "passphrase_confirm": "autrechose"},
        follow_redirects=True,
    )
    assert "ne correspondent pas" in r.data.decode()
    assert not store.is_initialized()


def test_deverrouiller_avec_bon_mot_de_passe(client, monkeypatch):
    _reset_backoff(monkeypatch)
    store.create_new("bonmotdepasse")
    store.lock()
    r = client.post("/deverrouiller", data={"passphrase": "bonmotdepasse"}, follow_redirects=True)
    assert r.status_code == 200
    assert store.is_unlocked()


def test_deverrouiller_avec_mauvais_mot_de_passe(client, monkeypatch):
    _reset_backoff(monkeypatch)
    store.create_new("bonmotdepasse")
    store.lock()
    r = client.post("/deverrouiller", data={"passphrase": "mauvais"}, follow_redirects=True)
    assert "incorrect" in r.data.decode()
    assert not store.is_unlocked()


def test_verrouiller_reverrouille_la_base(unlocked_client):
    assert store.is_unlocked()
    unlocked_client.post("/verrouiller", follow_redirects=True)
    assert not store.is_unlocked()


def test_page_protegee_redirige_si_verrouille(client):
    store.create_new("bonmotdepasse")
    store.lock()
    r = client.get("/annees", follow_redirects=False)
    assert r.status_code == 302
    assert "/deverrouiller" in r.headers["Location"]
