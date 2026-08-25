#!/bin/bash
# Démarre le service SpeedNote (s'il n'est pas déjà lancé) et ouvre l'application
# dans le navigateur par défaut.
set -e

systemctl --user start speednote.service

for _ in $(seq 1 20); do
    if curl -s -o /dev/null "http://127.0.0.1:8420/"; then
        break
    fi
    sleep 0.5
done

xdg-open "http://127.0.0.1:8420/" >/dev/null 2>&1 &
