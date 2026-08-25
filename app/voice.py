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

# Mots de ponctuation dictés -> signe (ou saut de ligne) correspondant. Les
# expressions les plus longues/spécifiques sont volontairement placées avant
# les mots génériques ("point", "virgule") qu'elles contiennent, pour être
# remplacées en premier (ex. "point d'exclamation" avant "point" seul).
# ["’]? tolère l'apostrophe manquante ou différente selon la transcription.
_PONCTUATION = [
    (re.compile(r"\bpoints?\s+de\s+suspension\b", re.IGNORECASE), "..."),
    (re.compile(r"\bpoint\s*d['’]?\s*exclamation\b", re.IGNORECASE), "!"),
    (re.compile(r"\bpoint\s*d['’]?\s*interrogation\b", re.IGNORECASE), "?"),
    (re.compile(r"\bpoint[\s-]virgule\b", re.IGNORECASE), ";"),
    (re.compile(r"\bdeux\s+points\b", re.IGNORECASE), ":"),
    (re.compile(r"\bvirgule\b", re.IGNORECASE), ","),
    (re.compile(r"\bpoint\b", re.IGNORECASE), "."),
    # "saut de ligne" avant "à la ligne" : aucun chevauchement entre les
    # deux, l'ordre n'a pas d'importance ici, mais autant grouper les sauts
    # de ligne ensemble.
    (re.compile(r"\bsaut\s+de\s+ligne\b", re.IGNORECASE), "\n\n"),
    (re.compile(r"\b[aà]\s+la\s+ligne\b", re.IGNORECASE), "\n"),
]


def _ponctuer(texte: str) -> str:
    """Convertit les mots de ponctuation/saut de ligne dictés ("point",
    "virgule", "à la ligne"...) en signes réels plutôt que de les laisser
    en toutes lettres."""
    for motif, signe in _PONCTUATION:
        texte = motif.sub(signe, texte)
    # Retire l'espace laissé avant le signe par le mot qu'il remplace.
    texte = re.sub(r"\s+([.,!?;:])", r"\1", texte)
    # Idem pour les espaces autour des sauts de ligne insérés.
    texte = re.sub(r"[ \t]*\n[ \t]*", "\n", texte)
    # Plafonne les sauts de ligne consécutifs à une seule ligne vide, même
    # si "à la ligne" et "saut de ligne" sont dictés à la suite l'un de l'autre.
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    return texte


_DEBUT_PHRASE_RE = re.compile(r"(^|[.!?]\s+|\n+)([a-zàâäéèêëïîôöùûüÿçñ])")


def _capitaliser_phrases(texte: str) -> str:
    """Met une majuscule en début de texte et après chaque signe de fin de
    phrase (. ! ?) ou saut de ligne — la reconnaissance vocale ne produit
    que du texte en minuscules."""
    return _DEBUT_PHRASE_RE.sub(lambda m: m.group(1) + m.group(2).upper(), texte)


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
    # La ponctuation dictée est convertie après ce nettoyage, pour que les
    # signes ajoutés ne soient jamais retirés par le strip() ci-dessus.
    appreciation = _ponctuer(appreciation).strip()
    appreciation = _capitaliser_phrases(appreciation)

    return {
        "eleve": eleve,
        "valeur": valeur,
        "appreciation": appreciation,
        "transcript": transcript,
    }
