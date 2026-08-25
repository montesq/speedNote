from datetime import date

from flask import Blueprint, redirect, render_template, request, url_for

from .. import periodes, store
from .eleves import add_eleves_bulk

bp = Blueprint("wizard", __name__)


def _annee_scolaire_suggeree() -> str:
    """Année scolaire par défaut proposée : N/N+1 à partir du 1er juillet
    de l'année N, sinon N-1/N (l'année scolaire en cours n'a pas encore basculé)."""
    aujourdhui = date.today()
    debut = aujourdhui.year if aujourdhui >= date(aujourdhui.year, 7, 1) else aujourdhui.year - 1
    return f"{debut}-{debut + 1}"


@bp.route("/wizard")
def accueil_wizard():
    conn = store.get_conn()
    annee = conn.execute(
        "SELECT * FROM annee_scolaire ORDER BY libelle DESC LIMIT 1"
    ).fetchone()
    classes = []
    if annee is not None:
        classes = conn.execute(
            """
            SELECT classe.*, COUNT(eleve.id) AS nb_eleves
            FROM classe
            LEFT JOIN eleve ON eleve.classe_id = classe.id
            WHERE classe.annee_scolaire_id = ?
            GROUP BY classe.id
            ORDER BY classe.nom
            """,
            (annee["id"],),
        ).fetchall()
    return render_template(
        "wizard.html",
        annee=annee,
        classes=classes,
        systemes=periodes.LIBELLES_SYSTEME,
        annee_suggeree=_annee_scolaire_suggeree(),
    )


@bp.route("/wizard/annee", methods=["POST"])
def creer_annee():
    conn = store.get_conn()
    libelle = request.form.get("libelle", "").strip()
    if libelle:
        conn.execute("INSERT INTO annee_scolaire (libelle) VALUES (?)", (libelle,))
        conn.commit()
        store.save()
    return redirect(url_for("wizard.accueil_wizard"))


@bp.route("/wizard/classes/<int:annee_id>", methods=["POST"])
def creer_classe(annee_id):
    conn = store.get_conn()
    nom = request.form.get("nom", "").strip()
    systeme_periode = periodes.systeme_valide(request.form.get("systeme_periode"))
    if nom:
        conn.execute(
            "INSERT INTO classe (annee_scolaire_id, nom, systeme_periode) VALUES (?, ?, ?)",
            (annee_id, nom, systeme_periode),
        )
        conn.commit()
        store.save()
    return redirect(url_for("wizard.accueil_wizard"))


@bp.route("/wizard/classes/<int:classe_id>/eleves", methods=["POST"])
def ajouter_eleves(classe_id):
    conn = store.get_conn()
    if add_eleves_bulk(conn, classe_id, request.form.get("bulk", "")):
        store.save()
    return redirect(url_for("wizard.accueil_wizard"))


@bp.route("/wizard/terminer", methods=["POST"])
def terminer():
    return redirect(url_for("accueil.index"))
