from markupsafe import escape

from app import store


def _creer_devoir(client, classe_id, **kwargs):
    data = {"titre": "Devoir", "coefficient": "1", "periode": "T1"}
    data.update(kwargs)
    client.post(
        f"/classes/{classe_id}/devoirs", data=data, content_type="multipart/form-data", follow_redirects=True
    )
    return store.get_conn().execute(
        "SELECT id FROM devoir WHERE titre = ?", (data["titre"],)
    ).fetchone()["id"]


def test_filtre_par_periode(unlocked_client, classe_id, eleve_id):
    d1 = _creer_devoir(unlocked_client, classe_id, titre="Devoir T1", periode="T1")
    d2 = _creer_devoir(unlocked_client, classe_id, titre="Devoir T2", periode="T2")

    html_t1 = unlocked_client.get(f"/classes/{classe_id}?periode=T1").data.decode()
    assert "Devoir T1" in html_t1
    assert "Devoir T2" not in html_t1

    html_t2 = unlocked_client.get(f"/classes/{classe_id}?periode=T2").data.decode()
    assert "Devoir T2" in html_t2
    assert "Devoir T1" not in html_t2


def test_filtre_par_type(unlocked_client, classe_id, eleve_id):
    _creer_devoir(unlocked_client, classe_id, titre="Devoir Oral", type="Oral")
    _creer_devoir(unlocked_client, classe_id, titre="Devoir Lecture", type="Lecture")

    html = unlocked_client.get(f"/classes/{classe_id}?periode=T1&type=Oral").data.decode()
    assert "Devoir Oral" in html
    assert "Devoir Lecture" not in html


def test_toutes_periodes_affiche_tout(unlocked_client, classe_id, eleve_id):
    _creer_devoir(unlocked_client, classe_id, titre="Devoir T1", periode="T1")
    _creer_devoir(unlocked_client, classe_id, titre="Devoir T2", periode="T2")

    html = unlocked_client.get(f"/classes/{classe_id}?periode=toutes").data.decode()
    assert "Devoir T1" in html
    assert "Devoir T2" in html


def test_type_invalide_ne_plante_pas(unlocked_client, classe_id):
    r = unlocked_client.get(f"/classes/{classe_id}?periode=T1&type=Bidule")
    assert r.status_code == 200


def test_moyenne_ponderee_par_coefficient(unlocked_client, classe_id, eleve_id):
    d1 = _creer_devoir(unlocked_client, classe_id, titre="Coef 1", coefficient="1")
    d2 = _creer_devoir(unlocked_client, classe_id, titre="Coef 3", coefficient="3")
    unlocked_client.post(f"/devoirs/{d1}/notes", data={"eleve_id": eleve_id, "valeur": "10"}, follow_redirects=True)
    unlocked_client.post(f"/devoirs/{d2}/notes", data={"eleve_id": eleve_id, "valeur": "16"}, follow_redirects=True)

    html = unlocked_client.get(f"/classes/{classe_id}?periode=T1").data.decode()
    # (10*1 + 16*3) / 4 = 14.5
    assert "14.5" in html


def test_moyenne_ignore_devoirs_non_notes(unlocked_client, classe_id, eleve_id):
    d1 = _creer_devoir(unlocked_client, classe_id, titre="Note", coefficient="1")
    _creer_devoir(unlocked_client, classe_id, titre="Sans note", coefficient="5")
    unlocked_client.post(f"/devoirs/{d1}/notes", data={"eleve_id": eleve_id, "valeur": "12"}, follow_redirects=True)

    html = unlocked_client.get(f"/classes/{classe_id}?periode=T1").data.decode()
    assert "12.0" in html or ">12<" in html


def test_type_titre_identique_pas_de_sous_titre_redondant(unlocked_client, classe_id, eleve_id):
    _creer_devoir(unlocked_client, classe_id, titre="Grammaire", type="Grammaire", coefficient="1")
    html = unlocked_client.get(f"/classes/{classe_id}?periode=T1").data.decode()
    devoir_id = store.get_conn().execute("SELECT id FROM devoir WHERE titre='Grammaire'").fetchone()["id"]
    assert f'href="/devoirs/{devoir_id}">Grammaire</a>' in html  # en-tête de colonne = le type
    # pas de repetition "Grammaire · coef." dans le sous-titre de la colonne
    assert "Grammaire · coef." not in html


def test_type_titre_different_affiche_le_sous_titre(unlocked_client, classe_id, eleve_id):
    _creer_devoir(
        unlocked_client, classe_id, titre="Le Rouge et le Noir", type="Commentaire", coefficient="2"
    )
    html = unlocked_client.get(f"/classes/{classe_id}?periode=T1").data.decode()
    assert str(escape("Le Rouge et le Noir")) + " · coef. 2" in html
