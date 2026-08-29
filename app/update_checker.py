"""Vérification périodique de mises à jour sur le dépôt git, et
application (téléchargement + réinstallation des dépendances). Le
redémarrage effectif est déclenché par l'appelant (route Flask), via
bin/redemarrer-speednote.sh, une fois le téléchargement réussi.

Limite connue : un changement de schéma de base de données dans une
mise à jour n'est pas migré automatiquement (comme pour tout
changement de schéma sur ce projet). À ne pas laisser tourner sans
surveillance tant qu'une vraie migration n'existe pas."""

import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CHECK_INTERVAL_SECONDS = 30 * 60

_lock = threading.RLock()
_etat = {"disponible": False, "resume": None, "erreur": None}


class MiseAJourError(Exception):
    """Erreur lors du téléchargement ou de l'installation d'une mise à jour."""


def _executer(cmd, timeout=30) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=timeout, check=False
    )


def _echouer(message: str) -> None:
    global _etat
    print(f"[update_checker] {message}", flush=True)
    with _lock:
        _etat = {"disponible": False, "resume": None, "erreur": message}


def _verifier_une_fois() -> None:
    global _etat
    try:
        fetch = _executer(["git", "fetch", "origin"], timeout=20)
        if fetch.returncode != 0:
            _echouer(
                "Impossible de vérifier les mises à jour (réseau ?) : "
                + (fetch.stderr.strip() or "erreur inconnue")
            )
            return

        amont = _executer(["git", "rev-parse", "@{u}"])
        if amont.returncode != 0:
            _echouer(
                "Aucune branche amont configurée : impossible de vérifier les mises à jour "
                "(git rev-parse @{u} : " + (amont.stderr.strip() or "erreur inconnue") + ")."
            )
            return

        # Nombre de commits présents en amont mais absents du HEAD local :
        # seul ce cas (amont en avance) correspond à une mise à jour
        # disponible. Une simple comparaison de hash déclencherait aussi
        # une fausse alerte quand c'est le local qui est en avance (commits
        # non poussés).
        nb_en_retard = _executer(["git", "rev-list", "--count", "HEAD..@{u}"]).stdout.strip()
        if nb_en_retard in ("", "0"):
            with _lock:
                _etat = {"disponible": False, "resume": None, "erreur": None}
            return

        resume = _executer(["git", "log", "-1", "--pretty=%s", "@{u}"]).stdout.strip()
        with _lock:
            _etat = {"disponible": True, "resume": resume, "erreur": None}
    except Exception as exc:
        _echouer(str(exc))


def etat() -> dict:
    with _lock:
        return dict(_etat)


def demarrer_verification_periodique() -> None:
    def boucle():
        while True:
            _verifier_une_fois()
            time.sleep(CHECK_INTERVAL_SECONDS)

    threading.Thread(target=boucle, daemon=True).start()


def appliquer_mise_a_jour() -> None:
    """git pull + réinstallation des dépendances. Ne redémarre pas :
    c'est à l'appelant de déclencher bin/redemarrer-speednote.sh une
    fois cette fonction revenue sans exception."""
    pull = _executer(["git", "pull", "--ff-only"], timeout=60)
    if pull.returncode != 0:
        raise MiseAJourError(
            "Échec du téléchargement : " + (pull.stderr.strip() or pull.stdout.strip() or "erreur inconnue")
        )

    pip_path = BASE_DIR / "venv" / "bin" / "pip"
    install = _executer(
        [str(pip_path), "install", "-r", str(BASE_DIR / "requirements.txt")], timeout=300
    )
    if install.returncode != 0:
        raise MiseAJourError(
            "Code téléchargé, mais l'installation des dépendances a échoué : "
            + (install.stderr.strip()[-500:] or "erreur inconnue")
        )

    with _lock:
        _etat["disponible"] = False
