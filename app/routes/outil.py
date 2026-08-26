from flask import Blueprint, jsonify, render_template, request

from .. import voice

bp = Blueprint("outil", __name__)


@bp.route("/outil")
def accueil():
    return render_template("outil.html")


@bp.route("/outil/transcrire", methods=["POST"])
def transcrire():
    audio_file = request.files.get("audio")
    if audio_file is None:
        return jsonify({"erreur": "Aucun enregistrement reçu."}), 400

    try:
        transcript = voice.transcribe(audio_file.read())
    except voice.TranscriptionError as exc:
        return jsonify({"erreur": str(exc)}), 500

    if not transcript:
        return jsonify({"erreur": "Rien n'a été compris. Réessayez en parlant plus fort et clairement."})

    return jsonify({"texte": voice.nettoyer_transcript(transcript)})
