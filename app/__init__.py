import os

from flask import Flask, redirect, request, url_for

from . import store, update_checker


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = _load_or_create_secret_key()
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 Mo (sujet joint, enregistrement vocal)

    from .routes.accueil import bp as accueil_bp
    from .routes.annees import bp as annees_bp
    from .routes.auth import bp as auth_bp
    from .routes.classes import bp as classes_bp
    from .routes.devoirs import bp as devoirs_bp
    from .routes.eleves import bp as eleves_bp
    from .routes.mise_a_jour import bp as mise_a_jour_bp
    from .routes.wizard import bp as wizard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(accueil_bp)
    app.register_blueprint(annees_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(eleves_bp)
    app.register_blueprint(devoirs_bp)
    app.register_blueprint(mise_a_jour_bp)
    app.register_blueprint(wizard_bp)

    ROUTES_LIBRES = ("auth.demarrage", "auth.deverrouiller", "static", "mise_a_jour.appliquer")

    @app.before_request
    def _guard():
        if request.endpoint in ROUTES_LIBRES:
            return None
        if not store.is_initialized():
            return redirect(url_for("auth.demarrage"))
        if not store.is_unlocked():
            return redirect(url_for("auth.deverrouiller"))
        return None

    @app.context_processor
    def inject_globals():
        annee_courante = None
        if store.is_unlocked():
            row = store.get_conn().execute(
                "SELECT libelle FROM annee_scolaire ORDER BY libelle DESC LIMIT 1"
            ).fetchone()
            annee_courante = row["libelle"] if row else None
        return {
            "store_unlocked": store.is_unlocked(),
            "mise_a_jour": update_checker.etat(),
            "annee_courante": annee_courante,
        }

    return app


def _load_or_create_secret_key() -> bytes:
    store.ensure_data_dir()
    key_path = store.DATA_DIR / "secret_key"
    if key_path.exists():
        return key_path.read_bytes()
    key = os.urandom(32)
    key_path.write_bytes(key)
    os.chmod(key_path, 0o600)
    return key
