import io
import time
from unittest.mock import patch

from app import store


def test_enregistrer_note_cree_avec_horodatage(unlocked_client, devoir_id, eleve_id):
    r = unlocked_client.post(
        f"/devoirs/{devoir_id}/notes",
        data={"eleve_id": eleve_id, "valeur": "15", "appreciation": "Bon travail"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    row = store.get_conn().execute(
        "SELECT * FROM note WHERE devoir_id = ? AND eleve_id = ?", (devoir_id, eleve_id)
    ).fetchone()
    assert row["valeur"] == 15.0
    assert row["appreciation"] == "Bon travail"
    assert row["cree_le"] == row["modifie_le"]


def test_enregistrer_note_mise_a_jour_garde_cree_le_et_avance_modifie_le(unlocked_client, devoir_id, eleve_id):
    unlocked_client.post(
        f"/devoirs/{devoir_id}/notes",
        data={"eleve_id": eleve_id, "valeur": "15", "appreciation": "Bon travail"},
        follow_redirects=True,
    )
    conn = store.get_conn()
    premiere = conn.execute(
        "SELECT cree_le, modifie_le FROM note WHERE devoir_id = ? AND eleve_id = ?", (devoir_id, eleve_id)
    ).fetchone()

    time.sleep(1.1)  # la granularité de datetime('now') est la seconde

    unlocked_client.post(
        f"/devoirs/{devoir_id}/notes",
        data={"eleve_id": eleve_id, "valeur": "17", "appreciation": "Très bon travail"},
        follow_redirects=True,
    )
    seconde = conn.execute(
        "SELECT cree_le, modifie_le, valeur FROM note WHERE devoir_id = ? AND eleve_id = ?", (devoir_id, eleve_id)
    ).fetchone()

    assert seconde["valeur"] == 17.0
    assert seconde["cree_le"] == premiere["cree_le"]
    assert seconde["modifie_le"] > premiere["modifie_le"]


def test_enregistrer_note_ne_touche_pas_les_autres_eleves(unlocked_client, devoir_id, classe_id):
    conn = store.get_conn()
    eleve_a = conn.execute(
        "INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, 'A', 'A')", (classe_id,)
    ).lastrowid
    eleve_b = conn.execute(
        "INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, 'B', 'B')", (classe_id,)
    ).lastrowid
    conn.commit()

    unlocked_client.post(
        f"/devoirs/{devoir_id}/notes", data={"eleve_id": eleve_a, "valeur": "10"}, follow_redirects=True
    )
    unlocked_client.post(
        f"/devoirs/{devoir_id}/notes", data={"eleve_id": eleve_b, "valeur": "20"}, follow_redirects=True
    )

    note_a = conn.execute("SELECT valeur FROM note WHERE eleve_id = ?", (eleve_a,)).fetchone()
    note_b = conn.execute("SELECT valeur FROM note WHERE eleve_id = ?", (eleve_b,)).fetchone()
    assert note_a["valeur"] == 10.0
    assert note_b["valeur"] == 20.0


def test_transcrire_appelle_le_parser_et_renvoie_json(unlocked_client, devoir_id, eleve_id):
    with patch("app.voice.transcribe", return_value="dupuis quinze bon travail"):
        r = unlocked_client.post(
            f"/devoirs/{devoir_id}/transcrire",
            data={"audio": (io.BytesIO(b"faux-audio"), "note.webm")},
            content_type="multipart/form-data",
        )
    assert r.status_code == 200
    data = r.get_json()
    assert data["eleve_id"] == eleve_id
    assert data["valeur"] == 15.0


def test_transcrire_rien_compris(unlocked_client, devoir_id):
    with patch("app.voice.transcribe", return_value=""):
        r = unlocked_client.post(
            f"/devoirs/{devoir_id}/transcrire",
            data={"audio": (io.BytesIO(b"faux-audio"), "note.webm")},
            content_type="multipart/form-data",
        )
    assert r.status_code == 200
    assert "erreur" in r.get_json()
