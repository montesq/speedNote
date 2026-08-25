CREATE TABLE annee_scolaire (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    libelle TEXT NOT NULL UNIQUE
);

CREATE TABLE classe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annee_scolaire_id INTEGER NOT NULL REFERENCES annee_scolaire(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    systeme_periode TEXT NOT NULL DEFAULT 'trimestre',
    UNIQUE(annee_scolaire_id, nom)
);

CREATE TABLE eleve (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classe_id INTEGER NOT NULL REFERENCES classe(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL DEFAULT ''
);

CREATE TABLE devoir (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classe_id INTEGER NOT NULL REFERENCES classe(id) ON DELETE CASCADE,
    titre TEXT NOT NULL,
    date_devoir TEXT,
    coefficient REAL NOT NULL DEFAULT 1,
    periode TEXT NOT NULL DEFAULT 'T1',
    type TEXT NOT NULL DEFAULT 'Commentaire',
    sous_type TEXT,
    sujet_nom_fichier TEXT,
    sujet_type_mime TEXT,
    sujet_fichier BLOB
);

CREATE TABLE note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    devoir_id INTEGER NOT NULL REFERENCES devoir(id) ON DELETE CASCADE,
    eleve_id INTEGER NOT NULL REFERENCES eleve(id) ON DELETE CASCADE,
    valeur REAL,
    appreciation TEXT,
    cree_le TEXT NOT NULL DEFAULT (datetime('now')),
    modifie_le TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(devoir_id, eleve_id)
);
