from flask import Blueprint, redirect, render_template, url_for

from .. import store

bp = Blueprint("accueil", __name__)


@bp.route("/")
def index():
    conn = store.get_conn()
    annee = conn.execute(
        "SELECT * FROM annee_scolaire ORDER BY libelle DESC LIMIT 1"
    ).fetchone()
    if annee is None:
        return redirect(url_for("wizard.accueil_wizard"))
    premiere_classe = conn.execute(
        "SELECT id FROM classe WHERE annee_scolaire_id = ? ORDER BY nom LIMIT 1",
        (annee["id"],),
    ).fetchone()
    if premiere_classe is None:
        return render_template("accueil.html", annee=annee)
    return redirect(url_for("classes.carnet", classe_id=premiere_classe["id"]))
