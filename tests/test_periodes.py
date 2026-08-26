from app import periodes


def test_systeme_valide_accepte_les_valeurs_connues():
    assert periodes.systeme_valide("trimestre") == "trimestre"
    assert periodes.systeme_valide("semestre") == "semestre"


def test_systeme_valide_replie_sur_trimestre_si_invalide():
    assert periodes.systeme_valide("bidule") == "trimestre"
    assert periodes.systeme_valide(None) == "trimestre"


def test_periodes_pour():
    assert periodes.periodes_pour("trimestre") == ["T1", "T2", "T3"]
    assert periodes.periodes_pour("semestre") == ["S1", "S2"]


def test_periode_par_defaut_sans_devoir_prend_la_premiere(unlocked_client, classe_id):
    from app import store

    conn = store.get_conn()
    classe = conn.execute("SELECT * FROM classe WHERE id = ?", (classe_id,)).fetchone()
    assert periodes.periode_par_defaut(conn, classe) == "T1"


def test_periode_par_defaut_avec_devoir_prend_celle_du_dernier(unlocked_client, classe_id):
    from app import store

    conn = store.get_conn()
    conn.execute(
        "INSERT INTO devoir (classe_id, titre, periode) VALUES (?, ?, ?)",
        (classe_id, "Devoir 1", "T2"),
    )
    conn.commit()
    classe = conn.execute("SELECT * FROM classe WHERE id = ?", (classe_id,)).fetchone()
    assert periodes.periode_par_defaut(conn, classe) == "T2"
