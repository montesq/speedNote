from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, url_for

from .. import periodes, rapports, store, voice

bp = Blueprint("devoirs", __name__)


@bp.route("/classes/<int:classe_id>/devoirs", methods=["POST"])
def creer(classe_id):
    conn = store.get_conn()
    classe = conn.execute("SELECT * FROM classe WHERE id = ?", (classe_id,)).fetchone()
    if classe is None:
        return redirect(url_for("accueil.index"))

    titre = request.form.get("titre", "").strip()
    date_devoir = request.form.get("date_devoir", "").strip()
    bareme_raw = request.form.get("bareme", "20").strip().replace(",", ".")
    try:
        bareme = float(bareme_raw) if bareme_raw else 20.0
    except ValueError:
        bareme = 20.0

    periode = request.form.get("periode", "")
    if periode not in periodes.periodes_pour(classe["systeme_periode"]):
        periode = periodes.periode_par_defaut(conn, classe)

    if titre:
        cur = conn.execute(
            "INSERT INTO devoir (classe_id, titre, date_devoir, bareme, periode) VALUES (?, ?, ?, ?, ?)",
            (classe_id, titre, date_devoir or None, bareme, periode),
        )
        conn.commit()
        store.save()
        return redirect(url_for("devoirs.saisie", devoir_id=cur.lastrowid))
    return redirect(url_for("classes.carnet", classe_id=classe_id, periode=periode))


@bp.route("/devoirs/<int:devoir_id>")
def saisie(devoir_id):
    conn = store.get_conn()
    devoir = conn.execute("SELECT * FROM devoir WHERE id = ?", (devoir_id,)).fetchone()
    if devoir is None:
        return redirect(url_for("annees.liste"))

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

    valeurs = [ligne["valeur"] for ligne in lignes if ligne["valeur"] is not None]
    moyenne = round(sum(valeurs) / len(valeurs), 2) if valeurs else None

    return render_template(
        "devoir_saisie.html", devoir=devoir, classe=classe, lignes=lignes, moyenne=moyenne
    )


@bp.route("/devoirs/<int:devoir_id>/rapports")
def generer_rapports(devoir_id):
    conn = store.get_conn()
    devoir = conn.execute("SELECT * FROM devoir WHERE id = ?", (devoir_id,)).fetchone()
    if devoir is None:
        return redirect(url_for("annees.liste"))

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

    if not lignes:
        return redirect(url_for("devoirs.saisie", devoir_id=devoir_id))

    pdf_bytes = rapports.generer_rapports(devoir, classe, lignes)
    filename = f"rapports-{rapports.slugifier(devoir['titre'])}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@bp.route("/devoirs/<int:devoir_id>/transcrire", methods=["POST"])
def transcrire(devoir_id):
    conn = store.get_conn()
    devoir = conn.execute("SELECT * FROM devoir WHERE id = ?", (devoir_id,)).fetchone()
    if devoir is None:
        return jsonify({"erreur": "Devoir introuvable."}), 404

    audio_file = request.files.get("audio")
    if audio_file is None:
        return jsonify({"erreur": "Aucun enregistrement reçu."}), 400

    eleves = conn.execute(
        "SELECT id, nom, prenom FROM eleve WHERE classe_id = ?", (devoir["classe_id"],)
    ).fetchall()

    try:
        transcript = voice.transcribe(audio_file.read())
    except voice.TranscriptionError as exc:
        return jsonify({"erreur": str(exc)}), 500

    if not transcript:
        return jsonify({
            "erreur": "Rien n'a été compris. Réessayez en parlant plus fort et clairement.",
        })

    resultat = voice.parser(transcript, eleves)
    eleve = resultat["eleve"]

    return jsonify({
        "eleve_id": eleve["id"] if eleve else None,
        "eleve_nom": f"{eleve['nom']} {eleve['prenom']}".strip() if eleve else None,
        "valeur": resultat["valeur"],
        "appreciation": resultat["appreciation"],
        "transcript": transcript,
    })


@bp.route("/devoirs/<int:devoir_id>/notes", methods=["POST"])
def enregistrer_note(devoir_id):
    """Enregistre la note/appréciation d'un seul élève (utilisé par la popup
    de commentaire vocal), sans toucher aux autres élèves du devoir."""
    conn = store.get_conn()
    devoir = conn.execute("SELECT * FROM devoir WHERE id = ?", (devoir_id,)).fetchone()
    if devoir is None:
        return redirect(url_for("annees.liste"))

    eleve_id = request.form.get("eleve_id", type=int)
    if eleve_id:
        eleve = conn.execute(
            "SELECT * FROM eleve WHERE id = ? AND classe_id = ?",
            (eleve_id, devoir["classe_id"]),
        ).fetchone()
        if eleve is not None:
            valeur_raw = request.form.get("valeur", "").strip().replace(",", ".")
            appreciation = request.form.get("appreciation", "").strip()
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
                (devoir_id, eleve_id, valeur, appreciation or None),
            )
            conn.commit()
            store.save()
            flash(f"✅ Note enregistrée pour {eleve['nom']} {eleve['prenom']}.")

    return redirect(url_for("devoirs.saisie", devoir_id=devoir_id))


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
        return redirect(url_for("classes.gerer", classe_id=row["classe_id"]))
    return redirect(url_for("annees.liste"))
