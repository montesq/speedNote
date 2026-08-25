"""Gestion des périodes (trimestres ou semestres) d'une classe."""

SYSTEMES = {
    "trimestre": ["T1", "T2", "T3"],
    "semestre": ["S1", "S2"],
}

LIBELLES_SYSTEME = {
    "trimestre": "Trimestres (T1, T2, T3)",
    "semestre": "Semestres (S1, S2)",
}


def systeme_valide(systeme):
    return systeme if systeme in SYSTEMES else "trimestre"


def periodes_pour(systeme):
    return SYSTEMES[systeme_valide(systeme)]


def periode_par_defaut(conn, classe):
    """Période à proposer pour un nouveau devoir, ou à afficher par défaut
    dans le carnet : celle du dernier devoir créé pour cette classe, sinon
    la première période du système de la classe."""
    row = conn.execute(
        "SELECT periode FROM devoir WHERE classe_id = ? ORDER BY id DESC LIMIT 1",
        (classe["id"],),
    ).fetchone()
    if row is not None:
        return row["periode"]
    return periodes_pour(classe["systeme_periode"])[0]
