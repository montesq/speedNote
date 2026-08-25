import time

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import store

bp = Blueprint("auth", __name__)

_failed_attempts = 0
_last_failure = 0.0


@bp.route("/demarrage", methods=["GET", "POST"])
def demarrage():
    if store.is_initialized():
        return redirect(url_for("auth.deverrouiller"))
    error = None
    if request.method == "POST":
        pw1 = request.form.get("passphrase", "")
        pw2 = request.form.get("passphrase_confirm", "")
        if len(pw1) < 8:
            error = "Le mot de passe doit contenir au moins 8 caractères."
        elif pw1 != pw2:
            error = "Les deux mots de passe ne correspondent pas."
        else:
            store.create_new(pw1)
            flash(
                "Base créée et déverrouillée avec votre mot de passe. "
                "Notez-le précieusement : il ne pourra pas être récupéré."
            )
            return redirect(url_for("annees.liste"))
    return render_template("demarrage.html", error=error)


@bp.route("/deverrouiller", methods=["GET", "POST"])
def deverrouiller():
    global _failed_attempts, _last_failure
    if not store.is_initialized():
        return redirect(url_for("auth.demarrage"))
    if store.is_unlocked():
        return redirect(url_for("annees.liste"))
    error = None
    if request.method == "POST":
        wait = _current_backoff()
        if wait > 0:
            error = f"Trop de tentatives, veuillez patienter {wait} secondes."
        else:
            pw = request.form.get("passphrase", "")
            if store.unlock(pw):
                _failed_attempts = 0
                return redirect(url_for("annees.liste"))
            _failed_attempts += 1
            _last_failure = time.monotonic()
            error = "Mot de passe incorrect."
    return render_template("deverrouiller.html", error=error)


def _current_backoff() -> int:
    if _failed_attempts == 0:
        return 0
    delay = min(2 ** (_failed_attempts - 1), 30)
    elapsed = time.monotonic() - _last_failure
    remaining = delay - elapsed
    return int(remaining) + 1 if remaining > 0 else 0


@bp.route("/verrouiller", methods=["POST"])
def verrouiller():
    store.lock()
    return redirect(url_for("auth.deverrouiller"))
