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
  l'application (à chaque démarrage, et de nouveau après 20 minutes
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
sudo apt install ffmpeg   # nécessaire pour le commentaire vocal
cd ~/Dev/SpeedNote
python3 -m venv venv
venv/bin/pip install -r requirements.txt
./scripts/download_vosk_model.sh   # modèle de reconnaissance vocale (~41 Mo, une seule fois)
```

## Utilisation au quotidien (raccourcis)

SpeedNote fonctionne comme une application de bureau classique : pas de
service système, pas de démarrage automatique avec l'ordinateur. Elle ne se
lance que lorsqu'on l'ouvre explicitement. Deux raccourcis sont installés
pour ça, dans le menu d'applications et sur le Bureau :

- **SpeedNote** — démarre l'application (si elle n'est pas déjà lancée) et
  ouvre automatiquement le navigateur sur http://127.0.0.1:8420. Il ne reste
  plus qu'à saisir le mot de passe maître.
- **Arrêter SpeedNote** — arrête l'application (les données restent, déjà
  chiffrées, sur le disque).

Si les icônes du Bureau demandent une confirmation au premier clic
(« Autoriser le lancement »), c'est normal la toute première fois — un clic
droit puis « Autoriser le lancement » suffit ensuite.

### Démarrage manuel en ligne de commande (équivalent aux raccourcis)

```bash
bin/demarrer-speednote.sh   # démarre l'application et ouvre le navigateur
bin/arreter-speednote.sh    # arrête l'application
```

Le PID du processus et ses logs sont dans `run/` (créé automatiquement, non
versionné).

### Réinstaller les raccourcis du Bureau (si besoin)

```bash
cd ~/Dev/SpeedNote
cp speednote-demarrer.desktop speednote-arreter.desktop ~/.local/share/applications/
cp speednote-demarrer.desktop speednote-arreter.desktop ~/Bureau/
chmod +x ~/Bureau/speednote-*.desktop ~/.local/share/applications/speednote-*.desktop
gio set ~/Bureau/speednote-demarrer.desktop "metadata::trusted" true
gio set ~/Bureau/speednote-arreter.desktop "metadata::trusted" true
```

## Sauvegardes

Le fichier `data/speednote.db.enc` (et sa copie précédente
`data/speednote.db.enc.bak`) contient toutes les données, déjà chiffrées :
c'est le seul fichier à sauvegarder régulièrement (par exemple en le copiant
sur une clé USB ou un espace de stockage externe). Une copie chiffrée ne
présente pas de risque de confidentialité en soi, mais nécessite toujours le
mot de passe maître pour être exploitée.

## Utilisation

### Première ouverture

Après la création du mot de passe maître, un petit assistant de configuration
s'affiche : il permet de créer la première année scolaire, puis d'ajouter les
classes (en choisissant pour chacune son système de périodes — trimestres ou
semestres) et, pour chacune, les élèves (un par ligne, "Nom Prénom"). Une fois
la configuration terminée, il n'est plus jamais montré — les mêmes réglages
restent accessibles à tout moment depuis **Admin**.

### Au quotidien

- L'écran d'accueil propose de choisir une classe.
- Chaque classe s'ouvre sur son **carnet de notes**, filtré par **période**
  (trimestre ou semestre selon la classe) : la liste des élèves, avec pour
  chaque devoir de la période la note obtenue. La période affichée par
  défaut est celle du dernier devoir saisi ; un menu déroulant permet d'en
  choisir une autre. C'est aussi depuis cet écran que se crée un nouveau
  **devoir** (titre, date, barème, période — pré-remplie avec la période du
  dernier devoir de la classe) — la création amène directement sur la
  grille de saisie note + appréciation par élève.
- Cliquer sur le titre d'un devoir dans le carnet rouvre cette grille pour
  corriger une note ou une appréciation.
- Sur la page d'un devoir, le bouton **🎤 Commentaire vocal** permet de
  dicter le nom de l'élève, sa note et une appréciation (ex. « Camille
  Dupuis, quatorze, bon travail mais peut approfondir l'analyse »). La
  reconnaissance vocale est **100% locale** (aucun son n'est envoyé sur
  Internet) : elle repère l'élève, remplit sa note et son appréciation
  directement dans la grille — à relire avant de cliquer sur
  "💾 Enregistrer", la reconnaissance n'étant pas parfaite.

### Admin

Le lien **Admin** (en haut de l'écran) donne accès aux écrans de
configuration : années scolaires, classes, élèves et suppression des
devoirs — pour ajouter une classe en cours d'année, gérer les élèves, ou
préparer l'année scolaire suivante.

## Développement : jeu de données de test

Pour explorer l'application sans repasser par l'assistant de configuration à
chaque fois, un script génère un jeu de données factices (une année, trois
classes, des élèves, des devoirs et des notes/appréciations variées) :

```bash
./bin/arreter-speednote.sh   # l'application doit être arrêtée
rm -rf data                  # repartir de zéro si une base existe déjà
venv/bin/python scripts/seed_demo.py
```

Mot de passe créé : `demo1234`. Ce script est un outil de développement — à
ne pas utiliser sur une base contenant de vraies données (il refuse
d'ailleurs de s'exécuter si `data/speednote.db.enc` existe déjà).
