from app import store


def test_creer_annee_scolaire(unlocked_client):
    r = unlocked_client.post("/annees", data={"libelle": "2026-2027"}, follow_redirects=True)
    assert r.status_code == 200
    row = store.get_conn().execute(
        "SELECT * FROM annee_scolaire WHERE libelle = ?", ("2026-2027",)
    ).fetchone()
    assert row is not None


def test_supprimer_annee_scolaire_cascade_les_classes(unlocked_client, annee_id, classe_id):
    conn = store.get_conn()
    assert conn.execute("SELECT COUNT(*) c FROM classe WHERE id = ?", (classe_id,)).fetchone()["c"] == 1

    unlocked_client.post(f"/annees/{annee_id}/supprimer", follow_redirects=True)

    assert conn.execute("SELECT COUNT(*) c FROM annee_scolaire WHERE id = ?", (annee_id,)).fetchone()["c"] == 0
    assert conn.execute("SELECT COUNT(*) c FROM classe WHERE id = ?", (classe_id,)).fetchone()["c"] == 0


def test_creer_classe(unlocked_client, annee_id):
    r = unlocked_client.post(
        f"/annees/{annee_id}/classes",
        data={"nom": "Terminale C", "systeme_periode": "semestre"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    row = store.get_conn().execute(
        "SELECT * FROM classe WHERE nom = ?", ("Terminale C",)
    ).fetchone()
    assert row is not None
    assert row["systeme_periode"] == "semestre"


def test_supprimer_classe_cascade_les_eleves(unlocked_client, classe_id, eleve_id):
    conn = store.get_conn()
    unlocked_client.post(f"/classes/{classe_id}/supprimer", follow_redirects=True)
    assert conn.execute("SELECT COUNT(*) c FROM eleve WHERE id = ?", (eleve_id,)).fetchone()["c"] == 0


def test_ajouter_eleves_en_masse(unlocked_client, classe_id):
    r = unlocked_client.post(
        f"/classes/{classe_id}/eleves",
        data={"bulk": "Dupont Marie\nMartin Lucas\n\nSeulNom"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    eleves = store.get_conn().execute(
        "SELECT nom, prenom FROM eleve WHERE classe_id = ? ORDER BY nom", (classe_id,)
    ).fetchall()
    noms = {(e["nom"], e["prenom"]) for e in eleves}
    assert ("Dupont", "Marie") in noms
    assert ("Martin", "Lucas") in noms
    assert ("SeulNom", "") in noms
    assert len(eleves) == 3  # la ligne vide est ignorée


def test_modifier_eleve(unlocked_client, eleve_id):
    unlocked_client.post(
        f"/eleves/{eleve_id}/modifier",
        data={"nom": "Nouveaunom", "prenom": "Nouveauprenom"},
        follow_redirects=True,
    )
    row = store.get_conn().execute("SELECT * FROM eleve WHERE id = ?", (eleve_id,)).fetchone()
    assert row["nom"] == "Nouveaunom"
    assert row["prenom"] == "Nouveauprenom"


def test_modifier_eleve_nom_vide_est_ignore(unlocked_client, eleve_id):
    conn = store.get_conn()
    avant = conn.execute("SELECT nom FROM eleve WHERE id = ?", (eleve_id,)).fetchone()["nom"]
    unlocked_client.post(f"/eleves/{eleve_id}/modifier", data={"nom": "", "prenom": "X"}, follow_redirects=True)
    apres = conn.execute("SELECT nom FROM eleve WHERE id = ?", (eleve_id,)).fetchone()["nom"]
    assert avant == apres


def test_supprimer_eleve(unlocked_client, eleve_id):
    unlocked_client.post(f"/eleves/{eleve_id}/supprimer", follow_redirects=True)
    row = store.get_conn().execute("SELECT * FROM eleve WHERE id = ?", (eleve_id,)).fetchone()
    assert row is None
