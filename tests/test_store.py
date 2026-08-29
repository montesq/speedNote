"""Tests du choix du dossier de données (app/store.py)."""

from app import store


def test_data_dir_par_defaut_est_a_cote_de_lapplication(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "CONF_PATH", tmp_path / "conf.ini")  # absent

    assert store._resolve_data_dir() == store.BASE_DIR / "data"


def test_data_dir_configurable_via_conf_ini(monkeypatch, tmp_path):
    """data_dir dans conf.ini doit permettre de déplacer la base et la clé
    secrète hors du dossier de l'application (ex. disque externe)."""
    ailleurs = tmp_path / "ailleurs" / "sous-dossier"
    conf = tmp_path / "conf.ini"
    conf.write_text(f"[speednote]\ndata_dir = {ailleurs}\n", encoding="utf-8")
    monkeypatch.setattr(store, "CONF_PATH", conf)

    assert store._resolve_data_dir() == ailleurs.resolve()


def test_data_dir_expanse_le_tilde(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    conf = tmp_path / "conf.ini"
    conf.write_text("[speednote]\ndata_dir = ~/mes-donnees-speednote\n", encoding="utf-8")
    monkeypatch.setattr(store, "CONF_PATH", conf)

    assert store._resolve_data_dir() == (tmp_path / "mes-donnees-speednote").resolve()


def test_data_dir_ligne_vide_ou_commentee_utilise_le_defaut(monkeypatch, tmp_path):
    conf = tmp_path / "conf.ini"
    conf.write_text("[speednote]\n# data_dir = /pas/actif\n", encoding="utf-8")
    monkeypatch.setattr(store, "CONF_PATH", conf)

    assert store._resolve_data_dir() == store.BASE_DIR / "data"


def test_data_dir_sans_section_speednote_utilise_le_defaut(monkeypatch, tmp_path):
    conf = tmp_path / "conf.ini"
    conf.write_text("[autre_section]\nfoo = bar\n", encoding="utf-8")
    monkeypatch.setattr(store, "CONF_PATH", conf)

    assert store._resolve_data_dir() == store.BASE_DIR / "data"
