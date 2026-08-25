# SpeedNote

Application locale de saisie des notes et appréciations, par année scolaire,
classe et devoir.

## Sécurité — à lire avant utilisation

- L'application n'écoute que sur `127.0.0.1` : elle n'est accessible que
  depuis un navigateur sur cet ordinateur, jamais depuis le réseau.
- Les données ne sont **jamais stockées en clair sur le disque**. Le fichier
  `data/speednote.db.enc` est chiffré (AES-256-GCM) avec une clé dérivée du
  mot de passe maître. Cette clé n'est jamais écrite sur disque : sans le mot
  de passe, le fichier est illisible.
- **Le mot de passe maître doit être saisi à chaque ouverture** de
  l'application (au démarrage du service, et de nouveau après 20 minutes
  d'inactivité ou un clic sur "Verrouiller").
- **Ce mot de passe n'est récupérable par personne.** S'il est oublié, les
  données sont définitivement perdues — notez-le dans un endroit sûr (par
  exemple un gestionnaire de mots de passe).
- Limite assumée : ce modèle protège les données *au repos* (ordinateur
  éteint/verrouillé, copie du fichier, vol du disque). Il ne protège pas
  contre quelqu'un qui aurait un accès actif à la session pendant que
  l'application est déverrouillée.

## Installation

```bash
cd ~/Dev/SpeedNote
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Démarrage manuel (test, sans service)

```bash
venv/bin/python run.py
```

Puis ouvrir http://127.0.0.1:8420 dans un navigateur sur cet ordinateur.
Au premier lancement, l'application demande de créer le mot de passe maître.

## Utilisation au quotidien (raccourcis)

L'application tourne comme un service systemd utilisateur, **volontairement
désactivé au démarrage de l'ordinateur** : elle ne se lance jamais toute
seule, il faut l'ouvrir explicitement. Deux raccourcis sont installés pour
ça, dans le menu d'applications et sur le Bureau :

- **SpeedNote** — démarre l'application et ouvre automatiquement le
  navigateur sur http://127.0.0.1:8420. Il ne reste plus qu'à saisir le mot
  de passe maître.
- **Arrêter SpeedNote** — arrête l'application (les données restent, déjà
  chiffrées, sur le disque).

Si les icônes du Bureau demandent une confirmation au premier clic
(« Autoriser le lancement »), c'est normal la toute première fois — un clic
droit puis « Autoriser le lancement » suffit ensuite.

### Réinstaller les raccourcis (si besoin)

```bash
cd ~/Dev/SpeedNote
mkdir -p ~/.config/systemd/user
cp speednote.service ~/.config/systemd/user/
systemctl --user daemon-reload

cp speednote-demarrer.desktop speednote-arreter.desktop ~/.local/share/applications/
cp speednote-demarrer.desktop speednote-arreter.desktop ~/Bureau/
chmod +x ~/Bureau/speednote-*.desktop ~/.local/share/applications/speednote-*.desktop
gio set ~/Bureau/speednote-demarrer.desktop "metadata::trusted" true
gio set ~/Bureau/speednote-arreter.desktop "metadata::trusted" true
```

### Commandes en ligne de commande (équivalentes aux raccourcis)

```bash
systemctl --user start speednote.service      # démarrer l'application
systemctl --user stop speednote.service       # arrêter l'application
systemctl --user status speednote.service     # état du service
journalctl --user -u speednote -f             # logs en direct
```

## Sauvegardes

Le fichier `data/speednote.db.enc` (et sa copie précédente
`data/speednote.db.enc.bak`) contient toutes les données, déjà chiffrées :
c'est le seul fichier à sauvegarder régulièrement (par exemple en le copiant
sur une clé USB ou un espace de stockage externe). Une copie chiffrée ne
présente pas de risque de confidentialité en soi, mais nécessite toujours le
mot de passe maître pour être exploitée.

## Utilisation

1. Créer une **année scolaire** (ex. « 2025-2026 »).
2. Dans l'année, créer une ou plusieurs **classes**.
3. Dans une classe, ajouter les **élèves** (un par ligne, "Nom Prénom").
4. Créer un **devoir** (titre, date, barème), puis saisir note et
   appréciation pour chaque élève dans la grille — la touche Entrée passe au
   champ suivant, et enregistre automatiquement en fin de tableau.
