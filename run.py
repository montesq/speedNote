from waitress import serve

from app import create_app, update_checker

app = create_app()

if __name__ == "__main__":
    update_checker.demarrer_verification_periodique()
    serve(app, host="127.0.0.1", port=8420)
