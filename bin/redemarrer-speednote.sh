#!/bin/bash
# Redémarre SpeedNote sans rouvrir automatiquement le navigateur — utilisé
# en interne par la mise à jour automatique (l'utilisateur est déjà
# devant l'application, pas besoin d'un nouvel onglet).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
cd "$APP_DIR"

mkdir -p run
PIDFILE="run/speednote.pid"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    kill "$(cat "$PIDFILE")"
fi
rm -f "$PIDFILE"

# Attend que l'ancien processus libère le port avant d'en relancer un.
for _ in $(seq 1 20); do
    if ! curl -s -o /dev/null "http://127.0.0.1:8420/"; then
        break
    fi
    sleep 0.3
done

nohup "$APP_DIR/venv/bin/python" "$APP_DIR/run.py" > run/speednote.log 2>&1 &
echo $! > "$PIDFILE"
