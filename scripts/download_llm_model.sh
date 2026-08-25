#!/bin/bash
# Télécharge le petit modèle de langage local (Llama 3.2 1B Instruct,
# quantisé Q4_K_M, ~770 Mo), utilisé pour générer le bilan de synthèse
# d'un élève sur une période. 100% hors-ligne après téléchargement.
# Idempotent : ne retélécharge rien si le modèle est déjà présent.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$APP_DIR/models"
MODEL_FILE="Llama-3.2-1B-Instruct-Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/${MODEL_FILE}"

mkdir -p "$MODELS_DIR"

if [ -f "$MODELS_DIR/$MODEL_FILE" ]; then
    echo "Le modèle $MODEL_FILE est déjà installé dans $MODELS_DIR/$MODEL_FILE"
    exit 0
fi

echo "Téléchargement de $MODEL_FILE (~770 Mo)..."
TMP_FILE="$(mktemp --suffix=.gguf)"
trap 'rm -f "$TMP_FILE"' EXIT

curl -L --fail --progress-bar -o "$TMP_FILE" "$MODEL_URL"
mv "$TMP_FILE" "$MODELS_DIR/$MODEL_FILE"
trap - EXIT

echo "Modèle installé dans $MODELS_DIR/$MODEL_FILE"
