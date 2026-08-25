#!/bin/bash
# Télécharge et installe le petit modèle français de reconnaissance vocale
# Vosk (~41 Mo), utilisé pour la transcription des commentaires vocaux.
# Idempotent : ne retélécharge rien si le modèle est déjà présent.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$APP_DIR/models"
MODEL_NAME="vosk-model-small-fr-0.22"
MODEL_URL="https://alphacephei.com/vosk/models/${MODEL_NAME}.zip"

mkdir -p "$MODELS_DIR"

if [ -d "$MODELS_DIR/$MODEL_NAME" ]; then
    echo "Le modèle $MODEL_NAME est déjà installé dans $MODELS_DIR/$MODEL_NAME"
    exit 0
fi

echo "Téléchargement de $MODEL_NAME (~41 Mo)..."
TMP_ZIP="$(mktemp --suffix=.zip)"
trap 'rm -f "$TMP_ZIP"' EXIT

curl -L --fail --progress-bar -o "$TMP_ZIP" "$MODEL_URL"

echo "Décompression..."
unzip -q "$TMP_ZIP" -d "$MODELS_DIR"

echo "Modèle installé dans $MODELS_DIR/$MODEL_NAME"
