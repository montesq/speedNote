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
def carnet(classe_id):
    """Écran par défaut : élèves de la classe, note pour chaque devoir."""
    conn = store.get_conn()
    classe = conn.execute("SELECT * FROM classe WHERE id = ?", (classe_id,)).fetchone()
    if classe is None:
        return redirect(url_for("accueil.index"))
    classes_annee = conn.execute(
        "SELECT * FROM classe WHERE annee_scolaire_id = ? ORDER BY nom",
        (classe["annee_scolaire_id"],),
    ).fetchall()
    eleves = conn.execute(
        "SELECT * FROM eleve WHERE classe_id = ? ORDER BY nom, prenom", (classe_id,)
    ).fetchall()
    devoirs = conn.execute(
        "SELECT * FROM devoir WHERE classe_id = ? ORDER BY date_devoir, id", (classe_id,)
    ).fetchall()

    notes_map = {}
    if devoirs:
        devoir_ids = [d["id"] for d in devoirs]
        placeholders = ",".join("?" * len(devoir_ids))
        rows = conn.execute(
            f"SELECT devoir_id, eleve_id, valeur FROM note WHERE devoir_id IN ({placeholders})",
            devoir_ids,
        ).fetchall()
        for row in rows:
            notes_map[(row["devoir_id"], row["eleve_id"])] = row["valeur"]

    def note_cellule(devoir, eleve_id):
        valeur = notes_map.get((devoir["id"], eleve_id))
        css = ""
        if valeur is not None and devoir["bareme"]:
            ratio = valeur / devoir["bareme"]
            css = "note-bonne" if ratio >= 0.7 else "note-moyenne" if ratio >= 0.5 else "note-faible"
        return {"valeur": valeur, "css": css}

    lignes = [
        {"eleve": e, "notes": [note_cellule(d, e["id"]) for d in devoirs]}
        for e in eleves
    ]
    return render_template(
        "classe_carnet.html",
        classe=classe,
        classes_annee=classes_annee,
        eleves=eleves,
        devoirs=devoirs,
        lignes=lignes,
    )


@bp.route("/classes/<int:classe_id>/gerer")
def gerer(classe_id):
    """Écran d'administration : élèves et devoirs de la classe."""
    conn = store.get_conn()
    classe = conn.execute("SELECT * FROM classe WHERE id = ?", (classe_id,)).fetchone()
    if classe is None:
        return redirect(url_for("accueil.index"))
    eleves = conn.execute(
        "SELECT * FROM eleve WHERE classe_id = ? ORDER BY nom, prenom", (classe_id,)
    ).fetchall()
    devoirs = conn.execute(
        "SELECT * FROM devoir WHERE classe_id = ? ORDER BY date_devoir DESC, id DESC",
        (classe_id,),
    ).fetchall()
    return render_template("classe_gerer.html", classe=classe, eleves=eleves, devoirs=devoirs)


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
