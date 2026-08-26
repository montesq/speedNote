"""Fixtures partagées : chaque test tourne sur une base chiffrée isolée
dans un dossier temporaire (jamais sur data/ du dépôt)."""

import pytest

from app import create_app, store

PASSPHRASE = "test1234"


@pytest.fixture
def app(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(store, "DATA_DIR", data_dir)
    monkeypatch.setattr(store, "DB_ENC_PATH", data_dir / "speednote.db.enc")
    monkeypatch.setattr(store, "DB_BAK_PATH", data_dir / "speednote.db.enc.bak")

    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    yield flask_app

    store.lock()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def unlocked_client(client):
    """Base fraîchement créée et déverrouillée (mot de passe PASSPHRASE)."""
    store.create_new(PASSPHRASE)
    client.post("/deverrouiller", data={"passphrase": PASSPHRASE}, follow_redirects=True)
    return client


@pytest.fixture
def annee_id(unlocked_client):
    conn = store.get_conn()
    cur = conn.execute("INSERT INTO annee_scolaire (libelle) VALUES (?)", ("2025-2026",))
    conn.commit()
    store.save()
    return cur.lastrowid


@pytest.fixture
def classe_id(annee_id):
    conn = store.get_conn()
    cur = conn.execute(
        "INSERT INTO classe (annee_scolaire_id, nom, systeme_periode) VALUES (?, ?, ?)",
        (annee_id, "1re B", "trimestre"),
    )
    conn.commit()
    store.save()
    return cur.lastrowid


@pytest.fixture
def eleve_id(classe_id):
    conn = store.get_conn()
    cur = conn.execute(
        "INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, ?, ?)",
        (classe_id, "Dupuis", "Léa"),
    )
    conn.commit()
    store.save()
    return cur.lastrowid


@pytest.fixture
def devoir_id(classe_id):
    conn = store.get_conn()
    cur = conn.execute(
        "INSERT INTO devoir (classe_id, titre, coefficient, periode, type) VALUES (?, ?, ?, ?, ?)",
        (classe_id, "Dissertation", 2, "T1", "Dissertation"),
    )
    conn.commit()
    store.save()
    return cur.lastrowid
