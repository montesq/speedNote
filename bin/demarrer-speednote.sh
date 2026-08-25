#!/bin/bash
# Démarre SpeedNote (s'il n'est pas déjà lancé) et ouvre l'application dans
# le navigateur par défaut. Aucun service système : c'est un simple
# processus, comme n'importe quelle application de bureau.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
cd "$APP_DIR"

mkdir -p run
PIDFILE="run/speednote.pid"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    : # déjà lancé
else
    nohup "$APP_DIR/venv/bin/python" "$APP_DIR/run.py" > run/speednote.log 2>&1 &
    echo $! > "$PIDFILE"
fi

for _ in $(seq 1 20); do
    if curl -s -o /dev/null "http://127.0.0.1:8420/"; then
        break
    fi
    sleep 0.5
done

xdg-open "http://127.0.0.1:8420/" >/dev/null 2>&1 &
