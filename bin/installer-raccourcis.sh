#!/bin/bash
# Installe (ou réinstalle) les raccourcis .desktop de SpeedNote avec le bon
# chemin absolu, quel que soit l'endroit où le projet a été cloné. Les
# fichiers speednote-*.desktop du dépôt sont des gabarits (__APP_DIR__ à
# remplacer), on ne les copie donc jamais tels quels.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

DEST_MENU="$HOME/.local/share/applications"
DEST_BUREAU="$HOME/Bureau"

mkdir -p "$DEST_MENU"

for nom in speednote-demarrer.desktop speednote-arreter.desktop; do
    sed "s#__APP_DIR__#$APP_DIR#g" "$APP_DIR/$nom" > "$DEST_MENU/$nom"
    chmod +x "$DEST_MENU/$nom"

    if [ -d "$DEST_BUREAU" ]; then
        sed "s#__APP_DIR__#$APP_DIR#g" "$APP_DIR/$nom" > "$DEST_BUREAU/$nom"
        chmod +x "$DEST_BUREAU/$nom"
        command -v gio >/dev/null 2>&1 && gio set "$DEST_BUREAU/$nom" "metadata::trusted" true || true
    fi
done

echo "Raccourcis installés dans $DEST_MENU$( [ -d "$DEST_BUREAU" ] && echo " et $DEST_BUREAU")."
