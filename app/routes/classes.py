from flask import Blueprint, redirect, render_template, request, url_for

from .. import periodes, store

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
        systeme_periode = periodes.systeme_valide(request.form.get("systeme_periode"))
        if nom:
            conn.execute(
                "INSERT INTO classe (annee_scolaire_id, nom, systeme_periode) VALUES (?, ?, ?)",
                (annee_id, nom, systeme_periode),
            )
            conn.commit()
            store.save()
        return redirect(url_for("classes.liste", annee_id=annee_id))
    classes = conn.execute(
        "SELECT * FROM classe WHERE annee_scolaire_id = ? ORDER BY nom", (annee_id,)
    ).fetchall()
    return render_template(
        "classes.html", annee=annee, classes=classes, systemes=periodes.LIBELLES_SYSTEME
    )


@bp.route("/classes/<int:classe_id>")
def carnet(classe_id):
    """Écran par défaut : élèves de la classe, note pour chaque devoir d'une période."""
    conn = store.get_conn()
    classe = conn.execute("SELECT * FROM classe WHERE id = ?", (classe_id,)).fetchone()
    if classe is None:
        return redirect(url_for("accueil.index"))
    classes_annee = conn.execute(
        "SELECT * FROM classe WHERE annee_scolaire_id = ? ORDER BY nom",
        (classe["annee_scolaire_id"],),
    ).fetchall()

    periodes_disponibles = periodes.periodes_pour(classe["systeme_periode"])
    periode_defaut = periodes.periode_par_defaut(conn, classe)
    periode = request.args.get("periode")
    if periode not in periodes_disponibles:
        periode = periode_defaut

    eleves = conn.execute(
        "SELECT * FROM eleve WHERE classe_id = ? ORDER BY nom, prenom", (classe_id,)
    ).fetchall()
    devoirs = conn.execute(
        "SELECT * FROM devoir WHERE classe_id = ? AND periode = ? ORDER BY date_devoir, id",
        (classe_id, periode),
    ).fetchall()

    notes_map = {}
    if devoirs:
        devoir_ids = [d["id"] for d in devoirs]
        placeholders = ",".join("?" * len(devoir_ids))
        rows = conn.execute(
            f"SELECT devoir_id, eleve_id, valeur, appreciation FROM note WHERE devoir_id IN ({placeholders})",
            devoir_ids,
        ).fetchall()
        for row in rows:
            notes_map[(row["devoir_id"], row["eleve_id"])] = row

    def note_cellule(devoir, eleve_id):
        entry = notes_map.get((devoir["id"], eleve_id))
        valeur = entry["valeur"] if entry else None
        appreciation = entry["appreciation"] if entry else None
        css = ""
        if valeur is not None:
            ratio = valeur / 20
            css = "note-bonne" if ratio >= 0.7 else "note-moyenne" if ratio >= 0.5 else "note-faible"
        return {
            "valeur": valeur,
            "appreciation": appreciation,
            "css": css,
            "devoir_titre": devoir["titre"],
        }

    def moyenne_eleve(notes):
        """Moyenne pondérée de l'élève sur la période (coefficient de chaque devoir)."""
        pondere = [
            (n["valeur"], d["coefficient"])
            for n, d in zip(notes, devoirs)
            if n["valeur"] is not None
        ]
        total_coef = sum(c for _, c in pondere)
        if not pondere or not total_coef:
            return None
        return round(sum(v * c for v, c in pondere) / total_coef, 2)

    lignes = []
    for e in eleves:
        notes = [note_cellule(d, e["id"]) for d in devoirs]
        lignes.append({"eleve": e, "notes": notes, "moyenne": moyenne_eleve(notes)})

    moyennes_devoirs = []
    for d in devoirs:
        valeurs = [
            entry["valeur"]
            for entry in (notes_map.get((d["id"], e["id"])) for e in eleves)
            if entry is not None and entry["valeur"] is not None
        ]
        moyennes_devoirs.append(round(sum(valeurs) / len(valeurs), 2) if valeurs else None)

    moyennes_eleves = [ligne["moyenne"] for ligne in lignes if ligne["moyenne"] is not None]
    moyenne_classe_periode = (
        round(sum(moyennes_eleves) / len(moyennes_eleves), 2) if moyennes_eleves else None
    )

    return render_template(
        "classe_carnet.html",
        classe=classe,
        classes_annee=classes_annee,
        periodes_disponibles=periodes_disponibles,
        periode=periode,
        periode_defaut=periode_defaut,
        eleves=eleves,
        devoirs=devoirs,
        lignes=lignes,
        moyennes_devoirs=moyennes_devoirs,
        moyenne_classe_periode=moyenne_classe_periode,
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
