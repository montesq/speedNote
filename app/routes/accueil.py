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
    classes = conn.execute(
        "SELECT * FROM classe WHERE annee_scolaire_id = ? ORDER BY nom", (annee["id"],)
    ).fetchall()
    return render_template("accueil.html", annee=annee, classes=classes)
