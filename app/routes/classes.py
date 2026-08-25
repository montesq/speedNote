from flask import Blueprint, redirect, render_template, request, url_for

from .. import store

bp = Blueprint("classes", __name__)


@bp.route("/annees/<int:annee_id>/classes", methods=["GET", "POST"])
def liste(annee_id):
    conn = store.get_conn()
    annee = conn.execute(
        "SELECT * FROM annee_scolaire WHERE id = ?", (annee_id,)
    ).fetchone()
    if annee is None:
        return redirect(url_for("annees.liste"))
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        if nom:
            conn.execute(
                "INSERT INTO classe (annee_scolaire_id, nom) VALUES (?, ?)",
                (annee_id, nom),
            )
            conn.commit()
            store.save()
        return redirect(url_for("classes.liste", annee_id=annee_id))
    classes = conn.execute(
        "SELECT * FROM classe WHERE annee_scolaire_id = ? ORDER BY nom", (annee_id,)
    ).fetchall()
    return render_template("classes.html", annee=annee, classes=classes)


@bp.route("/classes/<int:classe_id>")
def detail(classe_id):
    conn = store.get_conn()
    classe = conn.execute("SELECT * FROM classe WHERE id = ?", (classe_id,)).fetchone()
    if classe is None:
        return redirect(url_for("annees.liste"))
    eleves = conn.execute(
        "SELECT * FROM eleve WHERE classe_id = ? ORDER BY nom, prenom", (classe_id,)
    ).fetchall()
    devoirs = conn.execute(
        "SELECT * FROM devoir WHERE classe_id = ? ORDER BY date_devoir DESC, id DESC",
        (classe_id,),
    ).fetchall()
    return render_template("classe.html", classe=classe, eleves=eleves, devoirs=devoirs)


@bp.route("/classes/<int:classe_id>/supprimer", methods=["POST"])
def supprimer(classe_id):
    conn = store.get_conn()
    row = conn.execute(
        "SELECT annee_scolaire_id FROM classe WHERE id = ?", (classe_id,)
    ).fetchone()
    conn.execute("DELETE FROM classe WHERE id = ?", (classe_id,))
    conn.commit()
    store.save()
    if row:
        return redirect(url_for("classes.liste", annee_id=row["annee_scolaire_id"]))
    return redirect(url_for("annees.liste"))
