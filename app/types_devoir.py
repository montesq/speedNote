"""Types (et sous-types) de devoir, à choisir à la création."""

TYPES = [
    "Commentaire",
    "Dissertation",
    "Connaissance",
    "Lecture",
    "Grammaire",
    "Oral",
    "Exposé",
    "Explication linéaire écrite",
    "Explication linéaire orale",
]

SOUS_TYPES = ["Plan détaillé", "Grande partie", "Introduction", "Conclusion"]

TYPES_AVEC_SOUS_TYPE = {"Commentaire", "Dissertation"}


def type_valide(type_):
    return type_ if type_ in TYPES else TYPES[0]


def sous_type_valide(type_, sous_type):
    if type_ not in TYPES_AVEC_SOUS_TYPE:
        return None
    return sous_type if sous_type in SOUS_TYPES else None
