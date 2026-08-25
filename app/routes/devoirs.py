from flask import Blueprint, redirect, render_template, request, url_for

from .. import store

bp = Blueprint("devoirs", __name__)


@bp.route("/classes/<int:classe_id>/devoirs", methods=["POST"])
def creer(classe_id):
    conn = store.get_conn()
    titre = request.form.get("titre", "").strip()
    date_devoir = request.form.get("date_devoir", "").strip()
    bareme_raw = request.form.get("bareme", "20").strip().replace(",", ".")
    try:
        bareme = float(bareme_raw) if bareme_raw else 20.0
    except ValueError:
        bareme = 20.0
    if titre:
        cur = conn.execute(
            "INSERT INTO devoir (classe_id, titre, date_devoir, bareme) VALUES (?, ?, ?, ?)",
            (classe_id, titre, date_devoir or None, bareme),
        )
        conn.commit()
        store.save()
        return redirect(url_for("devoirs.saisie", devoir_id=cur.lastrowid))
    return redirect(url_for("classes.detail", classe_id=classe_id))


@bp.route("/devoirs/<int:devoir_id>", methods=["GET", "POST"])
def saisie(devoir_id):
    conn = store.get_conn()
    devoir = conn.execute("SELECT * FROM devoir WHERE id = ?", (devoir_id,)).fetchone()
    if devoir is None:
        return redirect(url_for("annees.liste"))

    if request.method == "POST":
        eleves = conn.execute(
            "SELECT id FROM eleve WHERE classe_id = ?", (devoir["classe_id"],)
        ).fetchall()
        for eleve in eleves:
            eid = eleve["id"]
            valeur_raw = request.form.get(f"note_{eid}", "").strip().replace(",", ".")
            appreciation = request.form.get(f"app_{eid}", "").strip()
            valeur = None
            if valeur_raw:
                try:
                    valeur = float(valeur_raw)
                except ValueError:
                    valeur = None
            conn.execute(
                """
                INSERT INTO note (devoir_id, eleve_id, valeur, appreciation)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(devoir_id, eleve_id)
                DO UPDATE SET valeur = excluded.valeur, appreciation = excluded.appreciation
                """,
                (devoir_id, eid, valeur, appreciation or None),
            )
        conn.commit()
        store.save()
        return redirect(url_for("devoirs.saisie", devoir_id=devoir_id))

    classe = conn.execute(
        "SELECT * FROM classe WHERE id = ?", (devoir["classe_id"],)
    ).fetchone()
    lignes = conn.execute(
        """
        SELECT eleve.id AS eleve_id, eleve.nom, eleve.prenom,
               note.valeur, note.appreciation
        FROM eleve
        LEFT JOIN note ON note.eleve_id = eleve.id AND note.devoir_id = ?
        WHERE eleve.classe_id = ?
        ORDER BY eleve.nom, eleve.prenom
        """,
        (devoir_id, devoir["classe_id"]),
    ).fetchall()
    return render_template("devoir_saisie.html", devoir=devoir, classe=classe, lignes=lignes)


@bp.route("/devoirs/<int:devoir_id>/supprimer", methods=["POST"])
def supprimer(devoir_id):
    conn = store.get_conn()
    row = conn.execute(
        "SELECT classe_id FROM devoir WHERE id = ?", (devoir_id,)
    ).fetchone()
    conn.execute("DELETE FROM devoir WHERE id = ?", (devoir_id,))
    conn.commit()
    store.save()
    if row:
        return redirect(url_for("classes.detail", classe_id=row["classe_id"]))
    return redirect(url_for("annees.liste"))
