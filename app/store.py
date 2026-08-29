"""Cycle de vie de la base SQLite en mémoire (verrouillage/déverrouillage).

La base ne réside jamais en clair sur le disque : seule une version chiffrée
(app.crypto) est écrite, après chaque modification, dans data/speednote.db.enc.
"""

import configparser
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from . import crypto

BASE_DIR = Path(__file__).resolve().parent.parent
CONF_PATH = BASE_DIR / "conf.ini"


def _load_config() -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    if CONF_PATH.exists():
        parser.read(CONF_PATH, encoding="utf-8")
    return parser


def _resolve_data_dir() -> Path:
    """Répertoire contenant la base chiffrée et la clé secrète. Par défaut
    data/ à côté de l'application, mais peut être déplacé (ex. clé USB,
    dossier synchronisé) via `data_dir` dans conf.ini (section
    [speednote]) — pratique quand data/ ne doit pas rester sur le disque
    interne de la machine. Voir conf.ini.example."""
    override = _load_config().get("speednote", "data_dir", fallback="").strip()
    if override:
        return Path(override).expanduser().resolve()
    return BASE_DIR / "data"


DATA_DIR = _resolve_data_dir()
DB_ENC_PATH = DATA_DIR / "speednote.db.enc"
DB_BAK_PATH = DATA_DIR / "speednote.db.enc.bak"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

INACTIVITY_TIMEOUT_SECONDS = 20 * 60

_lock = threading.RLock()
_conn: Optional[sqlite3.Connection] = None
_passphrase: Optional[str] = None
_last_activity: float = 0.0


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(DATA_DIR, 0o700)
    except OSError:
        pass


def is_initialized() -> bool:
    return DB_ENC_PATH.exists()


def is_unlocked() -> bool:
    with _lock:
        _check_timeout_locked()
        return _conn is not None


def touch_activity() -> None:
    global _last_activity
    with _lock:
        _last_activity = time.monotonic()


def _check_timeout_locked() -> None:
    global _conn, _passphrase
    if _conn is not None and (time.monotonic() - _last_activity) > INACTIVITY_TIMEOUT_SECONDS:
        _conn.close()
        _conn = None
        _passphrase = None


def _new_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_new(passphrase: str) -> None:
    """Premier lancement : crée une base vide et l'enregistre chiffrée."""
    global _conn, _passphrase
    with _lock:
        conn = _new_connection()
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
        _conn = conn
        _passphrase = passphrase
        touch_activity()
        _persist_locked()


def unlock(passphrase: str) -> bool:
    global _conn, _passphrase
    if not DB_ENC_PATH.exists():
        return False
    blob = DB_ENC_PATH.read_bytes()
    try:
        plaintext = crypto.decrypt(blob, passphrase)
    except crypto.DecryptionError:
        return False
    with _lock:
        conn = _new_connection()
        conn.executescript(plaintext.decode("utf-8"))
        conn.commit()
        _conn = conn
        _passphrase = passphrase
        touch_activity()
    return True


def lock() -> None:
    global _conn, _passphrase
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None
        _passphrase = None


def get_conn() -> sqlite3.Connection:
    with _lock:
        _check_timeout_locked()
        if _conn is None:
            raise RuntimeError("base verrouillée")
        touch_activity()
        return _conn


def save() -> None:
    """Ré-exporte, re-chiffre et écrit sur disque. À appeler après toute écriture."""
    with _lock:
        if _conn is None or _passphrase is None:
            raise RuntimeError("base verrouillée")
        _persist_locked()


def _persist_locked() -> None:
    dump = "\n".join(_conn.iterdump()).encode("utf-8")
    blob = crypto.encrypt(dump, _passphrase)
    ensure_data_dir()
    if DB_ENC_PATH.exists():
        DB_ENC_PATH.replace(DB_BAK_PATH)
    tmp_path = DB_ENC_PATH.with_suffix(".tmp")
    tmp_path.write_bytes(blob)
    os.chmod(tmp_path, 0o600)
    tmp_path.replace(DB_ENC_PATH)
