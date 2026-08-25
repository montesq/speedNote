from flask import Blueprint, redirect, request, url_for

from .. import store

bp = Blueprint("eleves", __name__)


def add_eleves_bulk(conn, classe_id, bulk_text):
    """Ajoute des élèves depuis un texte "un par ligne, Nom Prénom". Retourne le nombre ajouté."""
    added = 0
    for line in bulk_text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        nom = parts[0]
        prenom = parts[1] if len(parts) > 1 else ""
        conn.execute(
            "INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, ?, ?)",
            (classe_id, nom, prenom),
        )
        added += 1
    if added:
        conn.commit()
    return added


@bp.route("/classes/<int:classe_id>/eleves", methods=["POST"])
def ajouter(classe_id):
    conn = store.get_conn()
    added = add_eleves_bulk(conn, classe_id, request.form.get("bulk", ""))
    if added:
        store.save()
    return redirect(url_for("classes.gerer", classe_id=classe_id))


@bp.route("/eleves/<int:eleve_id>/modifier", methods=["POST"])
def modifier(eleve_id):
    conn = store.get_conn()
    nom = request.form.get("nom", "").strip()
    prenom = request.form.get("prenom", "").strip()
    row = conn.execute(
        "SELECT classe_id FROM eleve WHERE id = ?", (eleve_id,)
    ).fetchone()
    if row and nom:
        conn.execute(
            "UPDATE eleve SET nom = ?, prenom = ? WHERE id = ?", (nom, prenom, eleve_id)
        )
        conn.commit()
        store.save()
    if row:
        return redirect(url_for("classes.gerer", classe_id=row["classe_id"]))
    return redirect(url_for("annees.liste"))


@bp.route("/eleves/<int:eleve_id>/supprimer", methods=["POST"])
def supprimer(eleve_id):
    conn = store.get_conn()
    row = conn.execute(
        "SELECT classe_id FROM eleve WHERE id = ?", (eleve_id,)
    ).fetchone()
    conn.execute("DELETE FROM eleve WHERE id = ?", (eleve_id,))
    conn.commit()
    store.save()
    if row:
        return redirect(url_for("classes.gerer", classe_id=row["classe_id"]))
    return redirect(url_for("annees.liste"))
