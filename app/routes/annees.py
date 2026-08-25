from flask import Blueprint, redirect, render_template, request, url_for

from .. import store

bp = Blueprint("annees", __name__)


@bp.route("/annees", methods=["GET", "POST"])
def liste():
    conn = store.get_conn()
    if request.method == "POST":
        libelle = request.form.get("libelle", "").strip()
        if libelle:
            conn.execute("INSERT INTO annee_scolaire (libelle) VALUES (?)", (libelle,))
            conn.commit()
            store.save()
        return redirect(url_for("annees.liste"))
    annees = conn.execute(
        "SELECT * FROM annee_scolaire ORDER BY libelle DESC"
    ).fetchall()
    return render_template("annees.html", annees=annees)


@bp.route("/annees/<int:annee_id>/supprimer", methods=["POST"])
def supprimer(annee_id):
    conn = store.get_conn()
    conn.execute("DELETE FROM annee_scolaire WHERE id = ?", (annee_id,))
    conn.commit()
    store.save()
    return redirect(url_for("annees.liste"))
