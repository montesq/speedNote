import subprocess
import threading
import time

from flask import Blueprint, jsonify

from .. import update_checker

bp = Blueprint("mise_a_jour", __name__)


@bp.route("/mise-a-jour/appliquer", methods=["POST"])
def appliquer():
    if not update_checker.etat()["disponible"]:
        return jsonify({"erreur": "Aucune mise à jour disponible."}), 400

    try:
        update_checker.appliquer_mise_a_jour()
    except update_checker.MiseAJourError as exc:
        return jsonify({"erreur": str(exc)}), 500

    def redemarrer():
        time.sleep(1)  # laisse le temps à la réponse HTTP de partir avant de couper le serveur
        subprocess.Popen(
            ["/bin/bash", str(update_checker.BASE_DIR / "bin" / "redemarrer-speednote.sh")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    threading.Thread(target=redemarrer, daemon=True).start()
    return jsonify({"ok": True})
