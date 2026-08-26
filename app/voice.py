"""Transcription vocale locale (Vosk). Deux usages : pré-remplir note et
appréciation depuis un enregistrement audio sur la page de saisie d'un
devoir (parser()), et l'outil de dictée générale (nettoyer_transcript()).

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
from spellchecker import SpellChecker
from text_to_num import alpha2digit

MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "vosk-model-small-fr-0.22"
SAMPLE_RATE = 16000

_model: Optional["vosk.Model"] = None
_spell: Optional[SpellChecker] = None
_spell_indisponible = False


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


def _get_spellchecker():
    """Charge le correcteur orthographique français (paresseux, une seule
    fois). Purement local — aucun appel réseau. En cas d'échec de
    chargement, la correction est simplement désactivée sans planter."""
    global _spell, _spell_indisponible
    if _spell is None and not _spell_indisponible:
        try:
            _spell = SpellChecker(language="fr")
        except Exception:
            _spell_indisponible = True
    return _spell


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


def _retirer_insensible_accents(texte: str, motif: str) -> str:
    """Retire toutes les occurrences de `motif` dans `texte`, en ignorant
    la casse et les accents (Vosk ne restitue pas toujours les accents des
    noms propres, ex. "traore" au lieu de "Traoré"). Le retrait se fait par
    position sur le texte original (non normalisé) : la normalisation
    accent/casse préserve la longueur caractère par caractère pour les
    lettres latines accentuées usuelles, donc les positions trouvées dans
    la version normalisée restent valides sur le texte d'origine."""
    motif_norm = _sans_accents(motif)
    if not motif_norm:
        return texte
    texte_norm = _sans_accents(texte)
    resultat = []
    i = 0
    longueur = len(motif_norm)
    while i < len(texte_norm):
        if texte_norm[i:i + longueur] == motif_norm:
            i += longueur
        else:
            resultat.append(texte[i])
            i += 1
    return "".join(resultat)


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


_MOT_RE = re.compile(r"[a-zàâäéèêëïîôöùûüÿçñ]+", re.IGNORECASE)


def _corriger_orthographe(texte: str) -> str:
    """Corrige les fautes probables (dues à la reconnaissance vocale ou à
    de vraies fautes de frappe) via un dictionnaire français local. Les
    mots déjà reconnus par le dictionnaire — y compris la plupart des noms
    propres usuels — ne sont jamais modifiés, pour limiter les faux positifs."""
    spell = _get_spellchecker()
    if spell is None:
        return texte

    def _corriger_mot(m):
        mot = m.group(0)
        if len(mot) < 3 or mot.lower() in spell:
            return mot
        correction = spell.correction(mot.lower())
        return correction if correction else mot

    return _MOT_RE.sub(_corriger_mot, texte)


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


def _nettoyer_texte(texte: str) -> str:
    """Nettoyage commun à parser() et nettoyer_transcript() : espaces,
    orthographe, ponctuation dictée, majuscules de phrase."""
    texte = re.sub(r"\s+", " ", texte).strip(" ,.-")
    texte = _corriger_orthographe(texte)
    # La ponctuation dictée est convertie après ce nettoyage, pour que les
    # signes ajoutés ne soient jamais retirés par le strip() ci-dessus.
    texte = _ponctuer(texte).strip()
    texte = _capitaliser_phrases(texte)
    return texte


def nettoyer_transcript(transcript: str) -> str:
    """Nettoie un transcript vocal brut pour un usage texte libre (l'outil
    de dictée générale) : nombres en chiffres, orthographe corrigée,
    ponctuation dictée convertie, phrases capitalisées. Contrairement à
    parser(), ne cherche ni élève ni note — pas de contexte devoir ici."""
    texte = alpha2digit(transcript, "fr")
    return _nettoyer_texte(texte)


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
                appreciation = _retirer_insensible_accents(appreciation, morceau)

    appreciation = _nettoyer_texte(appreciation)

    return {
        "eleve": eleve,
        "valeur": valeur,
        "appreciation": appreciation,
        "transcript": transcript,
    }
