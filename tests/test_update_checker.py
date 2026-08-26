"""Tests du vérificateur de mise à jour. Utilise un dépôt git isolé et
jetable (origin bare + clone) — ne touche jamais le vrai dépôt SpeedNote."""

import subprocess

import pytest

from app import update_checker


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


@pytest.fixture
def depot(tmp_path):
    """Un dépôt origin (bare) + un clone local, avec un commit initial déjà
    poussé et le suivi de branche configuré (comme un vrai `git clone`)."""
    origin = tmp_path / "origin.git"
    clone = tmp_path / "clone"
    _git(tmp_path, "init", "--bare", "-q", "-b", "main", str(origin))

    subprocess.run(["git", "clone", "-q", str(origin), str(clone)], check=True, capture_output=True)
    _git(clone, "config", "user.email", "test@test.local")
    _git(clone, "config", "user.name", "Test")
    (clone / "requirements.txt").write_text("flask\n")
    _git(clone, "add", "requirements.txt")
    _git(clone, "commit", "-q", "-m", "commit initial")
    _git(clone, "push", "-q", "origin", "main")
    _git(clone, "branch", "--set-upstream-to=origin/main", "main")

    return {"origin": origin, "clone": clone}


@pytest.fixture
def clone_pointe(depot, monkeypatch):
    """Pointe update_checker sur le clone isolé, avec un faux pip qui réussit
    toujours (on ne veut pas réellement installer quoi que ce soit)."""
    monkeypatch.setattr(update_checker, "BASE_DIR", depot["clone"])
    venv_bin = depot["clone"] / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    pip_factice = venv_bin / "pip"
    pip_factice.write_text("#!/bin/bash\nexit 0\n")
    pip_factice.chmod(0o755)
    return depot


def _pousser_nouveau_commit(clone_source, resume, contenu_requirements="flask\npyspellchecker\n"):
    """Simule une mise à jour distante : clone une deuxième fois l'origin,
    pousse un nouveau commit, comme le ferait un autre contributeur."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        clone2 = Path(tmp) / "clone2"
        subprocess.run(
            ["git", "clone", "-q", str(clone_source), str(clone2)], check=True, capture_output=True
        )
        _git(clone2, "config", "user.email", "test@test.local")
        _git(clone2, "config", "user.name", "Test")
        (clone2 / "requirements.txt").write_text(contenu_requirements)
        _git(clone2, "add", "requirements.txt")
        _git(clone2, "commit", "-q", "-m", resume)
        _git(clone2, "push", "-q", "origin", "main")


def test_aucune_mise_a_jour_si_le_depot_est_a_jour(clone_pointe):
    update_checker._verifier_une_fois()
    assert update_checker.etat() == {"disponible": False, "resume": None, "erreur": None}


def test_detecte_une_mise_a_jour_disponible(clone_pointe):
    _pousser_nouveau_commit(clone_pointe["origin"], "Nouvelle fonctionnalité")
    update_checker._verifier_une_fois()
    etat = update_checker.etat()
    assert etat["disponible"] is True
    assert etat["resume"] == "Nouvelle fonctionnalité"
    assert etat["erreur"] is None


def test_depot_git_absent_ne_plante_pas(tmp_path, monkeypatch):
    monkeypatch.setattr(update_checker, "BASE_DIR", tmp_path)  # pas un dépôt git
    update_checker._verifier_une_fois()
    etat = update_checker.etat()
    assert etat["disponible"] is False
    assert etat["erreur"] is not None


def test_appliquer_mise_a_jour_reussie(clone_pointe):
    _pousser_nouveau_commit(clone_pointe["origin"], "Version propre")
    update_checker._verifier_une_fois()
    assert update_checker.etat()["disponible"] is True

    update_checker.appliquer_mise_a_jour()

    assert update_checker.etat()["disponible"] is False
    assert (clone_pointe["clone"] / "requirements.txt").read_text() == "flask\npyspellchecker\n"


def test_appliquer_mise_a_jour_echoue_si_divergence_locale(clone_pointe):
    # commit local jamais poussé : rend le fast-forward impossible
    (clone_pointe["clone"] / "local.txt").write_text("modification locale")
    _git(clone_pointe["clone"], "add", "local.txt")
    _git(clone_pointe["clone"], "commit", "-q", "-m", "commit local non poussé")

    _pousser_nouveau_commit(clone_pointe["origin"], "Version distante concurrente")
    update_checker._verifier_une_fois()

    with pytest.raises(update_checker.MiseAJourError):
        update_checker.appliquer_mise_a_jour()
    # la mise à jour reste signalée comme disponible : rien n'a été appliqué
    assert update_checker.etat()["disponible"] is True


def test_appliquer_mise_a_jour_echoue_si_pip_echoue(clone_pointe):
    pip_factice = clone_pointe["clone"] / "venv" / "bin" / "pip"
    pip_factice.write_text("#!/bin/bash\necho 'echec simule' >&2\nexit 1\n")
    pip_factice.chmod(0o755)

    _pousser_nouveau_commit(clone_pointe["origin"], "Version avec dependance qui echoue")
    update_checker._verifier_une_fois()

    with pytest.raises(update_checker.MiseAJourError):
        update_checker.appliquer_mise_a_jour()

    # le code a bien ete telecharge malgre l'echec de pip
    assert "pyspellchecker" in (clone_pointe["clone"] / "requirements.txt").read_text()
    # mais l'etat reste "disponible" : rien ne doit redemarrer sur cette base
    assert update_checker.etat()["disponible"] is True


def test_banniere_visible_meme_verrouille(client, monkeypatch):
    """Le bandeau de mise à jour doit s'afficher même sur l'écran de
    déverrouillage — l'application de la mise à jour ne dépend pas de
    l'état de la base."""
    from app import store

    store.create_new("test1234")
    store.lock()
    monkeypatch.setattr(
        update_checker, "_etat", {"disponible": True, "resume": "Nouvelle version", "erreur": None}
    )

    r = client.get("/deverrouiller")
    html = r.data.decode()
    assert "Une nouvelle version de SpeedNote est disponible" in html
    assert "Nouvelle version" in html


def test_route_appliquer_accessible_sans_deverrouiller(client, monkeypatch):
    from app import store

    store.create_new("test1234")
    store.lock()
    monkeypatch.setattr(
        update_checker, "_etat", {"disponible": True, "resume": "x", "erreur": None}
    )
    monkeypatch.setattr(update_checker, "appliquer_mise_a_jour", lambda: None)
    monkeypatch.setattr("app.routes.mise_a_jour.subprocess.Popen", lambda *a, **k: None)

    r = client.post("/mise-a-jour/appliquer")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}


def test_route_appliquer_sans_mise_a_jour_disponible(unlocked_client, monkeypatch):
    monkeypatch.setattr(
        update_checker, "_etat", {"disponible": False, "resume": None, "erreur": None}
    )
    r = unlocked_client.post("/mise-a-jour/appliquer")
    assert r.status_code == 400


def test_route_appliquer_erreur_de_telechargement(unlocked_client, monkeypatch):
    monkeypatch.setattr(
        update_checker, "_etat", {"disponible": True, "resume": "x", "erreur": None}
    )

    def echoue():
        raise update_checker.MiseAJourError("Échec du téléchargement : conflit.")

    monkeypatch.setattr(update_checker, "appliquer_mise_a_jour", echoue)
    r = unlocked_client.post("/mise-a-jour/appliquer")
    assert r.status_code == 500
    assert "conflit" in r.get_json()["erreur"]
