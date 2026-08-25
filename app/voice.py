"""Transcription vocale locale (Vosk) pour pré-remplir note et appréciation
depuis un enregistrement audio, sur la page de saisie d'un devoir.

Tout se fait en mémoire : l'audio n'est jamais écrit sur le disque. La
reconnaissance est 100% hors-ligne (aucun appel réseau), cohérent avec le
reste de l'application.
"""

import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Optional

import vosk
from text_to_num import alpha2digit

MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "vosk-model-small-fr-0.22"
SAMPLE_RATE = 16000

_model: Optional["vosk.Model"] = None


class TranscriptionError(Exception):
    """Erreur lors de la conversion audio ou de la reconnaissance vocale."""


def _get_model():
    global _model
    if _model is None:
        if not MODEL_DIR.exists():
            raise TranscriptionError(
                "Modèle de reconnaissance vocale introuvable. "
                "Lancez scripts/download_vosk_model.sh."
            )
        vosk.SetLogLevel(-1)
        _model = vosk.Model(str(MODEL_DIR))
    return _model


def _to_pcm16(audio_bytes: bytes) -> bytes:
    try:
        proc = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-i", "pipe:0",
                "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1",
                "pipe:1",
            ],
            input=audio_bytes,
            capture_output=True,
            check=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise TranscriptionError("ffmpeg n'est pas installé sur cet ordinateur.") from exc
    except subprocess.CalledProcessError as exc:
        raise TranscriptionError("Impossible de lire l'enregistrement audio.") from exc
    return proc.stdout


def transcribe(audio_bytes: bytes) -> str:
    """Convertit un enregistrement audio (webm/opus...) en texte français."""
    pcm = _to_pcm16(audio_bytes)
    model = _get_model()
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.AcceptWaveform(pcm)
    result = json.loads(recognizer.FinalResult())
    return result.get("text", "").strip()


def _sans_accents(texte: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c)
    ).lower()


def _trouver_eleve(transcript_norm: str, eleves):
    """Cherche, parmi les élèves, celui dont le nom apparaît dans le transcript."""
    meilleur = None
    meilleure_longueur = 0
    for eleve in eleves:
        nom = _sans_accents(eleve["nom"])
        prenom = _sans_accents(eleve["prenom"]) if eleve["prenom"] else ""
        for candidat in (f"{prenom} {nom}", f"{nom} {prenom}", nom, prenom):
            candidat = candidat.strip()
            if candidat and candidat in transcript_norm and len(candidat) > meilleure_longueur:
                meilleur = eleve
                meilleure_longueur = len(candidat)
    return meilleur


_NOTE_RE = re.compile(r"\b(\d{1,2}(?:[.,]\d)?)\b")


def parser(transcript: str, eleves):
    """Extrait élève, note et appréciation d'un transcript vocal.

    Heuristique volontairement simple (pas fiable à 100%) : le résultat
    est toujours présenté en mode édition à l'utilisatrice avant tout
    enregistrement en base.
    """
    transcript_chiffres = alpha2digit(transcript, "fr")
    transcript_norm = _sans_accents(transcript_chiffres)

    eleve = _trouver_eleve(transcript_norm, eleves)

    valeur = None
    appreciation = transcript_chiffres
    match = _NOTE_RE.search(transcript_chiffres)
    if match:
        try:
            valeur = float(match.group(1).replace(",", "."))
        except ValueError:
            valeur = None
        appreciation = transcript_chiffres[: match.start()] + transcript_chiffres[match.end():]

    if eleve is not None:
        for morceau in (eleve["nom"], eleve["prenom"]):
            if morceau:
                appreciation = re.sub(re.escape(morceau), "", appreciation, flags=re.IGNORECASE)

    appreciation = re.sub(r"\s+", " ", appreciation).strip(" ,.-")
    if appreciation:
        appreciation = appreciation[0].upper() + appreciation[1:]

    return {
        "eleve": eleve,
        "valeur": valeur,
        "appreciation": appreciation,
        "transcript": transcript,
    }
