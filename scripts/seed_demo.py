#!/usr/bin/env python3
"""Remplit SpeedNote avec un jeu de données factices, pour tester l'application
sans repasser par l'assistant de configuration à chaque fois.

Outil de développement uniquement — n'a rien à voir avec l'usage réel de
l'application. L'application ne doit PAS être en cours d'exécution pendant
que ce script tourne (il écrit directement le fichier data/speednote.db.enc,
en dehors du processus serveur).

Usage :
    venv/bin/python scripts/seed_demo.py [mot_de_passe]

Mot de passe par défaut : demo1234
Si des données existent déjà (data/speednote.db.enc), le script refuse de
continuer — supprimez d'abord data/ (application arrêtée) pour repartir de
zéro.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import store  # noqa: E402

PASSPHRASE_DEFAULT = "demo1234"

CLASSES = {
    "2nde A": [
        ("Dupuis", "Camille"), ("Nguyen", "Léa"), ("Martin", "Hugo"),
        ("Bernard", "Inès"), ("Petit", "Nathan"), ("Robert", "Chloé"),
        ("Moreau", "Enzo"), ("Simon", "Manon"), ("Laurent", "Adam"),
        ("Lefebvre", "Jade"), ("Michel", "Louis"), ("Garcia", "Zoé"),
    ],
    "1re B": [
        ("Roux", "Sacha"), ("Fournier", "Lina"), ("Girard", "Tom"),
        ("Bonnet", "Emma"), ("Dupont", "Noah"), ("Lambert", "Rose"),
        ("Fontaine", "Léon"), ("Rousseau", "Alice"), ("Vincent", "Gabin"),
        ("Muller", "Anna"), ("Faure", "Timéo"), ("André", "Julia"),
    ],
    "Terminale C": [
        ("Blanc", "Maël"), ("Guerin", "Iris"), ("Boyer", "Paul"),
        ("Meyer", "Léna"),
    ],
}

DEVOIRS_PAR_CLASSE = {
    "2nde A": [
        ("Contrôle de lecture — Candide", "2025-09-22", 20),
        ("Explication linéaire n°1", "2025-10-10", 20),
        ("Dissertation — La Fontaine", "2025-11-14", 20),
    ],
    "1re B": [
        ("Commentaire — Les Fleurs du mal", "2025-09-18", 20),
        ("Question de grammaire", "2025-10-02", 10),
        ("Dissertation blanche", "2025-11-20", 20),
    ],
    "Terminale C": [
        ("Explication linéaire — Spleen", "2025-09-25", 20),
        ("Dissertation — Le roman", "2025-10-30", 20),
    ],
}

APPRECIATIONS_BONNES = [
    "Très bon travail, argumentation solide.",
    "Analyse fine et bien menée, continuez ainsi.",
    "Excellente maîtrise de la méthode.",
    "Copie claire et bien construite.",
]
APPRECIATIONS_MOYENNES = [
    "Des idées intéressantes mais à mieux structurer.",
    "Travail correct, attention à l'expression.",
    "Peut mieux faire : approfondissez l'analyse.",
    "Devoir sérieux mais manque de précision.",
]
APPRECIATIONS_FAIBLES = [
    "Relisez la méthode de la dissertation.",
    "Trop de hors-sujet, revoyez le cours.",
    "Travail insuffisant, à retravailler.",
    "Manque de rigueur dans l'argumentation.",
]


def note_et_appreciation(bareme, rng):
    if rng.random() < 0.08:
        return None, None
    valeur = round(rng.triangular(bareme * 0.35, bareme, bareme * 0.75), 1)
    ratio = valeur / bareme
    if ratio >= 0.7:
        appreciation = rng.choice(APPRECIATIONS_BONNES)
    elif ratio >= 0.5:
        appreciation = rng.choice(APPRECIATIONS_MOYENNES)
    else:
        appreciation = rng.choice(APPRECIATIONS_FAIBLES)
    return valeur, appreciation


def main():
    passphrase = sys.argv[1] if len(sys.argv) > 1 else PASSPHRASE_DEFAULT

    if store.is_initialized():
        print(f"Une base existe déjà dans {store.DATA_DIR} — annulé.")
        print("Arrêtez l'application puis supprimez data/ si vous voulez repartir de zéro.")
        return 1

    rng = random.Random(42)
    store.create_new(passphrase)
    conn = store.get_conn()

    cur = conn.execute("INSERT INTO annee_scolaire (libelle) VALUES (?)", ("2025-2026",))
    annee_id = cur.lastrowid

    for nom_classe, eleves in CLASSES.items():
        cur = conn.execute(
            "INSERT INTO classe (annee_scolaire_id, nom) VALUES (?, ?)",
            (annee_id, nom_classe),
        )
        classe_id = cur.lastrowid

        eleve_ids = []
        for nom, prenom in eleves:
            cur = conn.execute(
                "INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, ?, ?)",
                (classe_id, nom, prenom),
            )
            eleve_ids.append(cur.lastrowid)

        for titre, date_devoir, bareme in DEVOIRS_PAR_CLASSE[nom_classe]:
            cur = conn.execute(
                "INSERT INTO devoir (classe_id, titre, date_devoir, bareme) VALUES (?, ?, ?, ?)",
                (classe_id, titre, date_devoir, bareme),
            )
            devoir_id = cur.lastrowid

            for eleve_id in eleve_ids:
                valeur, appreciation = note_et_appreciation(bareme, rng)
                conn.execute(
                    "INSERT INTO note (devoir_id, eleve_id, valeur, appreciation) VALUES (?, ?, ?, ?)",
                    (devoir_id, eleve_id, valeur, appreciation),
                )

    conn.commit()
    store.save()

    print("Jeu de données factices créé avec succès.")
    print(f"  Mot de passe : {passphrase}")
    print(f"  Année : 2025-2026 — Classes : {', '.join(CLASSES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
