import io

from app import store


def test_creer_devoir_minimal(unlocked_client, classe_id):
    r = unlocked_client.post(
        f"/classes/{classe_id}/devoirs",
        data={"titre": "Dissertation", "coefficient": "2", "periode": "T1"},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    row = store.get_conn().execute(
        "SELECT * FROM devoir WHERE titre = ?", ("Dissertation",)
    ).fetchone()
    assert row is not None
    assert row["coefficient"] == 2.0
    assert row["periode"] == "T1"
    assert row["type"] == "Commentaire"  # défaut
    assert row["sous_type"] is None


def test_creer_devoir_sans_titre_ne_cree_rien(unlocked_client, classe_id):
    conn = store.get_conn()
    avant = conn.execute("SELECT COUNT(*) c FROM devoir").fetchone()["c"]
    unlocked_client.post(
        f"/classes/{classe_id}/devoirs",
        data={"titre": "", "coefficient": "1", "periode": "T1"},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    apres = conn.execute("SELECT COUNT(*) c FROM devoir").fetchone()["c"]
    assert avant == apres


def test_creer_devoir_avec_type_et_sous_type(unlocked_client, classe_id):
    unlocked_client.post(
        f"/classes/{classe_id}/devoirs",
        data={
            "titre": "Le Rouge et le Noir",
            "coefficient": "1",
            "periode": "T1",
            "type": "Commentaire",
            "sous_type": "Introduction",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    row = store.get_conn().execute(
        "SELECT * FROM devoir WHERE titre = ?", ("Le Rouge et le Noir",)
    ).fetchone()
    assert row["type"] == "Commentaire"
    assert row["sous_type"] == "Introduction"


def test_sous_type_ignore_si_type_ne_le_supporte_pas(unlocked_client, classe_id):
    unlocked_client.post(
        f"/classes/{classe_id}/devoirs",
        data={
            "titre": "Oral test",
            "coefficient": "1",
            "periode": "T1",
            "type": "Oral",
            "sous_type": "Introduction",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    row = store.get_conn().execute("SELECT * FROM devoir WHERE titre = ?", ("Oral test",)).fetchone()
    assert row["type"] == "Oral"
    assert row["sous_type"] is None


def test_creer_devoir_avec_sujet_joint_et_le_retelecharger(unlocked_client, classe_id):
    contenu = b"%PDF-1.4 contenu de test"
    unlocked_client.post(
        f"/classes/{classe_id}/devoirs",
        data={
            "titre": "Avec sujet",
            "coefficient": "1",
            "periode": "T1",
            "sujet": (io.BytesIO(contenu), "sujet.pdf", "application/pdf"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    devoir = store.get_conn().execute(
        "SELECT * FROM devoir WHERE titre = ?", ("Avec sujet",)
    ).fetchone()
    assert devoir["sujet_nom_fichier"] == "sujet.pdf"

    r = unlocked_client.get(f"/devoirs/{devoir['id']}/sujet")
    assert r.status_code == 200
    assert r.data == contenu
    assert r.content_type == "application/pdf"


def test_telecharger_sujet_absent_redirige_sans_erreur(unlocked_client, devoir_id):
    r = unlocked_client.get(f"/devoirs/{devoir_id}/sujet", follow_redirects=False)
    assert r.status_code == 302


def test_modifier_coefficient(unlocked_client, devoir_id):
    r = unlocked_client.post(f"/devoirs/{devoir_id}/coefficient", data={"coefficient": "3.5"})
    assert r.status_code == 200
    assert r.get_json()["coefficient"] == 3.5
    row = store.get_conn().execute("SELECT coefficient FROM devoir WHERE id = ?", (devoir_id,)).fetchone()
    assert row["coefficient"] == 3.5


def test_modifier_coefficient_invalide_est_rejete(unlocked_client, devoir_id):
    r = unlocked_client.post(f"/devoirs/{devoir_id}/coefficient", data={"coefficient": "abc"})
    assert r.status_code == 400


def test_modifier_coefficient_negatif_est_rejete(unlocked_client, devoir_id):
    r = unlocked_client.post(f"/devoirs/{devoir_id}/coefficient", data={"coefficient": "-1"})
    assert r.status_code == 400


def test_supprimer_devoir_cascade_les_notes(unlocked_client, devoir_id, eleve_id):
    conn = store.get_conn()
    conn.execute(
        "INSERT INTO note (devoir_id, eleve_id, valeur) VALUES (?, ?, ?)", (devoir_id, eleve_id, 15)
    )
    conn.commit()

    unlocked_client.post(f"/devoirs/{devoir_id}/supprimer", follow_redirects=True)

    assert conn.execute("SELECT COUNT(*) c FROM devoir WHERE id = ?", (devoir_id,)).fetchone()["c"] == 0
    assert conn.execute("SELECT COUNT(*) c FROM note WHERE devoir_id = ?", (devoir_id,)).fetchone()["c"] == 0


def test_page_saisie_classe_les_notes_par_couleur(unlocked_client, classe_id, devoir_id):
    conn = store.get_conn()
    bon = conn.execute("INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, 'Bon', 'E')", (classe_id,)).lastrowid
    moyen = conn.execute("INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, 'Moyen', 'E')", (classe_id,)).lastrowid
    faible = conn.execute("INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, 'Faible', 'E')", (classe_id,)).lastrowid
    sans_note = conn.execute("INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, 'Sansnote', 'E')", (classe_id,)).lastrowid
    conn.execute("INSERT INTO note (devoir_id, eleve_id, valeur) VALUES (?, ?, 15)", (devoir_id, bon))
    conn.execute("INSERT INTO note (devoir_id, eleve_id, valeur) VALUES (?, ?, 11)", (devoir_id, moyen))
    conn.execute("INSERT INTO note (devoir_id, eleve_id, valeur) VALUES (?, ?, 6)", (devoir_id, faible))
    conn.commit()

    html = unlocked_client.get(f"/devoirs/{devoir_id}").data.decode()

    import re

    def classe_de(nom):
        m = re.search(
            rf'data-eleve-nom="{nom} E"[\s\S]*?eleve-carte-valeur ([a-z\- ]*)"', html
        )
        return m.group(1).strip() if m else None

    assert classe_de("Bon") == "tag tag-accent"
    assert classe_de("Moyen") == "tag tag-neutral"
    assert classe_de("Faible") == "tag tag-outline"
    assert classe_de("Sansnote") == ""


def test_page_saisie_affiche_apercu_appreciation(unlocked_client, devoir_id, eleve_id):
    conn = store.get_conn()
    conn.execute(
        "INSERT INTO note (devoir_id, eleve_id, valeur, appreciation) VALUES (?, ?, 12, ?)",
        (devoir_id, eleve_id, "Bon travail dans l'ensemble."),
    )
    conn.commit()
    html = unlocked_client.get(f"/devoirs/{devoir_id}").data.decode()
    assert "Bon travail dans l&#39;ensemble." in html or "Bon travail dans l'ensemble." in html


def test_page_saisie_sans_appreciation_pas_apercu(unlocked_client, devoir_id, eleve_id):
    conn = store.get_conn()
    conn.execute("INSERT INTO note (devoir_id, eleve_id, valeur) VALUES (?, ?, 12)", (devoir_id, eleve_id))
    conn.commit()
    html = unlocked_client.get(f"/devoirs/{devoir_id}").data.decode()
    assert '<span class="eleve-carte-appreciation">' not in html
