"""Génération d'un bilan de synthèse (3 phrases) à partir des appréciations
d'un élève sur une période, via un petit modèle de langage local (Llama 3.2
1B Instruct, quantisé). 100% hors-ligne, cohérent avec le reste de
l'application : aucune donnée n'est jamais envoyée à un service tiers."""

from pathlib import Path
from typing import Optional

from llama_cpp import Llama

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "Llama-3.2-1B-Instruct-Q4_K_M.gguf"

_llm: Optional[Llama] = None

SYSTEME = (
    "Tu es un professeur de lettres au lycée qui rédige des synthèses pour "
    "le bulletin scolaire. Tu réponds uniquement par la synthèse demandée, "
    "en français, sans préambule ni liste à puces, en exactement 3 phrases "
    "fluides, bienveillantes mais honnêtes."
)


class BilanError(Exception):
    """Erreur lors de la génération du bilan."""


def _get_llm() -> Llama:
    global _llm
    if _llm is None:
        if not MODEL_PATH.exists():
            raise BilanError(
                "Modèle de synthèse introuvable. Lancez scripts/download_llm_model.sh."
            )
        _llm = Llama(model_path=str(MODEL_PATH), n_ctx=2048, n_threads=4, verbose=False)
    return _llm


def generer_bilan(nom_eleve: str, commentaires: list) -> str:
    """commentaires : liste de dicts avec devoir_titre, valeur, appreciation."""
    utiles = [c for c in commentaires if c.get("appreciation")]
    if not utiles:
        return "Aucune appréciation disponible pour générer un bilan."

    lignes = []
    for c in utiles:
        note = f"{c['valeur']}/20" if c.get("valeur") is not None else "non noté"
        lignes.append(f"- {c['devoir_titre']} ({note}) : {c['appreciation']}")
    corpus = "\n".join(lignes)

    llm = _get_llm()
    messages = [
        {"role": "system", "content": SYSTEME},
        {
            "role": "user",
            "content": (
                f"Voici les appréciations de {nom_eleve} sur la période, devoir par devoir :\n"
                f"{corpus}\n\n"
                "Rédige une synthèse en exactement 3 phrases pour le bulletin, qui dégage "
                "la tendance générale, les points forts et un axe de progrès."
            ),
        },
    ]

    try:
        resultat = llm.create_chat_completion(messages=messages, max_tokens=220, temperature=0.4)
    except Exception as exc:
        raise BilanError("Échec de la génération du bilan.") from exc

    texte = resultat["choices"][0]["message"]["content"].strip()
    if not texte:
        raise BilanError("Le modèle n'a produit aucun texte.")
    return texte
