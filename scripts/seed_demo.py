#!/usr/bin/env python3
"""Remplit SpeedNote avec un jeu de données factices, pour tester l'application
sans repasser par l'assistant de configuration à chaque fois.

Outil de développement uniquement — n'a rien à voir avec l'usage réel de
l'application. L'application ne doit PAS être en cours d'exécution pendant
que ce script tourne (il écrit directement le fichier data/speednote.db.enc,
en dehors du processus serveur).

Usage :
    venv/bin/python scripts/seed_demo.py [mot_de_passe]

Mot de passe par défaut : demo1234
Si des données existent déjà (data/speednote.db.enc), le script refuse de
continuer — supprimez d'abord data/ (application arrêtée) pour repartir de
zéro.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import store  # noqa: E402

PASSPHRASE_DEFAULT = "demo1234"

SYSTEME_PAR_CLASSE = {
    "2nde A": "trimestre",
    "1re B": "semestre",
    "Terminale C": "semestre",
}

CLASSES = {
    "2nde A": [
        ("Dupuis", "Camille"), ("Nguyen", "Léa"), ("Martin", "Hugo"),
        ("Bernard", "Inès"), ("Petit", "Nathan"), ("Robert", "Chloé"),
        ("Moreau", "Enzo"), ("Simon", "Manon"), ("Laurent", "Adam"),
        ("Lefebvre", "Jade"), ("Michel", "Louis"), ("Garcia", "Zoé"),
    ],
    "1re B": [
        ("Roux", "Sacha"), ("Fournier", "Lina"), ("Girard", "Tom"),
        ("Bonnet", "Emma"), ("Dupont", "Noah"), ("Lambert", "Rose"),
        ("Fontaine", "Léon"), ("Rousseau", "Alice"), ("Vincent", "Gabin"),
        ("Muller", "Anna"), ("Faure", "Timéo"), ("André", "Julia"),
    ],
    "Terminale C": [
        ("Blanc", "Maël"), ("Guerin", "Iris"), ("Boyer", "Paul"),
        ("Meyer", "Léna"),
    ],
}

DEVOIRS_PAR_CLASSE = {
    "2nde A": [
        ("Contrôle de lecture — Candide", "2025-09-22", 1, "T1"),
        ("Explication linéaire n°1", "2025-10-10", 1, "T1"),
        ("Dissertation — La Fontaine", "2025-11-14", 2, "T2"),
    ],
    "1re B": [
        ("Commentaire — Les Fleurs du mal", "2025-09-18", 2, "S1"),
        ("Question de grammaire", "2025-10-02", 1, "S1"),
        ("Dissertation blanche", "2025-11-20", 3, "S2"),
    ],
    "Terminale C": [
        ("Explication linéaire — Spleen", "2025-09-25", 2, "S1"),
        ("Dissertation — Le roman", "2025-10-30", 3, "S2"),
    ],
}

# Commentaires longs (~250-300 mots), représentatifs de la volumétrie réelle
# d'une appréciation détaillée de dissertation/commentaire/explication linéaire.
APPRECIATIONS_BONNES = [
    "Votre copie témoigne d'une lecture attentive et personnelle de l'œuvre. "
    "La problématique est clairement posée dès l'introduction et vous parvenez "
    "à maintenir un fil conducteur cohérent tout au long du devoir. Le plan "
    "choisi met bien en valeur les enjeux du sujet : chaque partie s'enchaîne "
    "logiquement et les transitions sont soignées, ce qui facilite grandement "
    "la lecture. J'apprécie particulièrement la finesse de votre analyse dans "
    "la deuxième partie, où vous croisez plusieurs citations pour étayer votre "
    "propos sans jamais tomber dans la paraphrase. Le choix des exemples est "
    "pertinent et vous montrez une réelle maîtrise des outils d'analyse "
    "littéraire (registres, figures de style, effets de rythme). L'expression "
    "est claire, le vocabulaire varié et précis, et l'on sent un effort "
    "constant pour éviter les répétitions. Quelques formulations restent "
    "toutefois un peu lourdes ; n'hésitez pas à relire votre texte à voix "
    "haute pour repérer les tournures maladroites. La conclusion ouvre "
    "intelligemment sur une perspective plus large, ce qui est appréciable, "
    "même si elle pourrait être développée un peu plus pour mieux clore la "
    "réflexion. Sur la forme, la copie est propre et bien présentée, ce qui "
    "facilite la correction. Continuez à travailler la nuance de votre "
    "pensée : vous avez tous les outils pour aller vers l'excellence, il ne "
    "manque qu'un peu plus d'audace dans l'interprétation personnelle des "
    "textes. Félicitations pour ce travail sérieux et abouti, qui montre une "
    "vraie progression depuis le début de l'année. Gardez ce niveau "
    "d'exigence pour les prochains devoirs, en particulier pour l'épreuve du "
    "baccalauréat qui demandera cette même rigueur méthodologique.",

    "Un devoir de très bonne facture, qui se distingue par la qualité de son "
    "argumentation. Dès les premières lignes, vous annoncez clairement votre "
    "plan et vous vous y tenez avec rigueur, ce qui donne une impression de "
    "maîtrise appréciable à la lecture. Chaque partie repose sur une idée "
    "directrice bien identifiée, illustrée par des exemples précis puisés "
    "aussi bien dans le texte que dans vos lectures personnelles, ce qui "
    "enrichit considérablement votre propos. La progression de la réflexion "
    "est logique : vous partez d'une lecture assez évidente du texte pour "
    "aller vers une interprétation plus nuancée et originale dans la "
    "troisième partie, ce qui est exactement ce qu'on attend à ce niveau. Le "
    "style est fluide, les phrases bien construites, et vous maîtrisez "
    "correctement les connecteurs logiques qui articulent votre "
    "démonstration. J'ai noté quelques maladresses de vocabulaire technique "
    "(le terme d'« énonciation » est employé un peu approximativement), mais "
    "cela ne nuit pas à la compréhension générale. La conclusion synthétise "
    "bien les grandes lignes de votre analyse et propose une ouverture "
    "pertinente vers une autre œuvre du mouvement littéraire étudié. "
    "L'orthographe est globalement maîtrisée, avec seulement quelques "
    "étourderies qui mériteraient une relecture plus attentive avant de "
    "rendre la copie. C'est un travail qui montre que la méthode est acquise "
    "et qu'il ne reste qu'à affiner la précision de l'expression pour "
    "atteindre l'excellence. La gestion du temps semble également avoir été "
    "bien anticipée, ce qui vous a permis de soigner chaque partie sans "
    "précipitation. Continuez ainsi, vous êtes sur la bonne voie pour les "
    "épreuves à venir.",

    "Excellente copie qui se lit avec un réel plaisir. Votre introduction "
    "pose le contexte de l'œuvre avec précision et amène la problématique de "
    "façon naturelle, sans lourdeur inutile. On sent que vous avez pris le "
    "temps de bien comprendre le sujet avant de vous lancer dans la "
    "rédaction, ce qui évite l'écueil du hors-sujet partiel que l'on "
    "rencontre trop souvent. Votre première partie établit solidement les "
    "bases de l'analyse, la deuxième l'approfondit avec des citations bien "
    "choisies et correctement analysées, et la troisième apporte un "
    "véritable dépassement de la question initiale — c'est cette dernière "
    "partie qui fait la différence et qui témoigne d'une réflexion "
    "personnelle aboutie. Vous manipulez avec aisance le vocabulaire de "
    "l'analyse littéraire et vos remarques sur la tonalité du texte sont "
    "particulièrement justes. Quelques répétitions de structure syntaxique "
    "pourraient être évitées en variant davantage vos amorces de phrase. La "
    "gestion du temps semble avoir été bien anticipée puisque la conclusion "
    "n'est pas bâclée, contrairement à ce qu'on observe souvent en fin "
    "d'épreuve. Je vous invite à présent à travailler la densité de vos "
    "paragraphes : certains passages, déjà très bons, gagneraient à être "
    "encore un peu plus étayés par des exemples supplémentaires puisés "
    "dans d'autres œuvres du même mouvement littéraire, ce qui montrerait "
    "une culture plus large encore. Un travail sérieux, régulier et "
    "exigeant, qui porte ses fruits et qui augure d'excellents résultats "
    "pour les épreuves à venir. Bravo, poursuivez sur cette lancée jusqu'à "
    "la fin de l'année.",
]
APPRECIATIONS_MOYENNES = [
    "Ce devoir contient des idées intéressantes mais souffre d'un manque de "
    "structuration qui nuit à la clarté de votre propos. L'introduction "
    "évoque bien le sujet mais la problématique reste floue, ce qui rend "
    "difficile de savoir précisément où vous souhaitez emmener le lecteur. "
    "Le plan en deux parties fonctionne globalement, mais certaines idées "
    "auraient mérité d'être développées davantage plutôt que juxtaposées "
    "sans réelle démonstration. Je note par exemple votre remarque sur le "
    "rythme de la phrase dans le deuxième paragraphe, qui est pertinente "
    "mais reste à l'état d'esquisse : il aurait fallu l'illustrer par une "
    "citation précise et en tirer une conclusion explicite. Le vocabulaire "
    "employé est correct mais assez pauvre par endroits, avec des "
    "répétitions du mot « montre » qui pourraient être évitées en variant "
    "les verbes d'analyse (« souligne », « met en évidence », « traduit »). "
    "L'expression manque parfois de fluidité, certaines phrases sont trop "
    "longues et perdent le lecteur en cours de route. La conclusion est "
    "trop courte et se contente de résumer sans ouvrir sur une perspective "
    "nouvelle. Pour progresser, je vous conseille de travailler "
    "systématiquement au brouillon la formulation de votre problématique "
    "avant de rédiger, et de vous assurer que chaque paragraphe défend "
    "une seule idée clairement énoncée en phrase d'attaque. Revoyez "
    "également la méthode de la citation analysée vue en cours : citer "
    "n'est utile que si l'on commente ensuite précisément le procédé "
    "d'écriture repéré. Prenez également le temps de constituer une fiche "
    "de vocabulaire d'analyse à réviser avant chaque devoir, cela vous "
    "évitera bien des répétitions maladroites. Ce travail reste correct "
    "mais doit gagner en rigueur et en précision pour la suite de "
    "l'année.",

    "Un travail sérieux dans son intention mais qui peine à convaincre sur "
    "le fond. Vous avez visiblement compris le sujet dans ses grandes "
    "lignes, mais l'analyse reste trop souvent en surface : vous décrivez "
    "ce que fait le texte sans toujours expliquer comment ni pourquoi, ce "
    "qui limite la portée de votre démonstration. La première partie est "
    "la plus convaincante, avec une lecture assez fine du passage étudié, "
    "mais la deuxième s'essouffle et multiplie les affirmations non "
    "démontrées. Attention à ne pas confondre paraphrase et analyse : "
    "reformuler le texte avec d'autres mots n'apporte rien si l'on n'en "
    "tire pas une interprétation. Sur la forme, l'expression est correcte "
    "dans l'ensemble, mais on relève plusieurs fautes d'accord qui "
    "trahissent un manque de relecture (les participes passés notamment "
    "méritent votre vigilance). Les transitions entre les parties sont "
    "abruptes, presque inexistantes par endroits, ce qui casse la "
    "progression de votre raisonnement. Je vous engage à retravailler la "
    "construction de vos paragraphes selon la méthode vue en classe : idée "
    "directrice, citation, analyse du procédé, interprétation. C'est cette "
    "dernière étape qui fait souvent défaut dans votre copie. La "
    "conclusion, bien que présente, ne fait que reprendre les grandes "
    "lignes sans réelle valeur ajoutée. Avec un travail plus régulier sur "
    "la méthode et davantage d'entraînement à l'analyse détaillée des "
    "extraits, vous avez la capacité de progresser nettement. Je vous "
    "conseille de reprendre systématiquement vos devoirs corrigés pour "
    "identifier les erreurs récurrentes et éviter de les reproduire. Ne "
    "vous découragez pas, la marge de progression est réelle.",

    "Devoir moyen qui laisse une impression mitigée. Les idées de fond ne "
    "sont pas inintéressantes, mais leur mise en forme laisse à désirer. Le "
    "plan annoncé en introduction n'est pas exactement celui suivi dans le "
    "développement, ce qui perturbe la lecture et donne le sentiment d'une "
    "improvisation. Certains paragraphes traitent en réalité de la même "
    "idée sous des angles très proches, ce qui donne une impression de "
    "redite plutôt que de progression. J'ai relevé de bonnes intuitions, "
    "notamment sur le lien entre la forme du texte et son sens, mais "
    "celles-ci ne sont jamais pleinement exploitées : vous les mentionnez "
    "puis passez à autre chose sans les développer. Le style d'écriture "
    "est globalement clair, même si le niveau de langue reste parfois trop "
    "familier pour un exercice de ce type. Pensez à bannir les tournures "
    "orales et les approximations lexicales. La gestion du temps semble "
    "avoir posé problème : la fin du devoir est visiblement rédigée dans "
    "la précipitation, avec des phrases inachevées et une conclusion "
    "expédiée en quelques lignes. Je vous recommande de vous entraîner à "
    "la gestion du temps d'épreuve en vous chronométrant lors des devoirs "
    "maison, et de toujours réserver au moins dix minutes pour la "
    "relecture finale. Sur le fond, revoyez la distinction entre "
    "argument et exemple, qui reste imprécise dans votre copie, ainsi que "
    "la façon d'articuler plusieurs arguments entre eux pour construire "
    "une véritable démonstration progressive. Un travail à consolider, "
    "mais les bases méthodologiques sont là.",
]
APPRECIATIONS_FAIBLES = [
    "Ce devoir pose de sérieuses difficultés qu'il convient de traiter sans "
    "attendre. Le sujet n'est que partiellement compris : votre "
    "introduction reformule la consigne sans dégager de véritable "
    "problématique, ce qui rend l'ensemble du devoir difficile à suivre. "
    "Le plan est peu lisible, les parties ne sont pas clairement "
    "identifiées et les idées se succèdent sans lien logique apparent. On "
    "trouve davantage un résumé du texte qu'une analyse : vous racontez ce "
    "qui se passe sans jamais expliquer les choix d'écriture de l'auteur "
    "ni leur effet sur le lecteur. Les citations, quand elles sont "
    "présentes, ne sont pas intégrées à la phrase et ne sont suivies "
    "d'aucun commentaire, ce qui les rend inutiles. L'expression pose "
    "également problème : de nombreuses phrases sont mal construites, le "
    "vocabulaire est pauvre et répétitif, et plusieurs fautes "
    "d'orthographe et de conjugaison viennent perturber la lecture. La "
    "conclusion est absente ou se limite à une phrase très générale qui ne "
    "clôt pas réellement la réflexion. Il est indispensable de revoir "
    "entièrement la méthode de l'exercice avec le cours et de vous "
    "entraîner sur des sujets similaires avant la prochaine évaluation. Je "
    "vous propose de venir me voir pour reprendre ensemble la structure "
    "attendue et les attentes précises de l'exercice. Ne restez pas seul "
    "face à ces difficultés : avec un travail ciblé sur la méthode et un "
    "entraînement régulier sur des sujets courts, une nette amélioration "
    "est tout à fait possible d'ici la fin du trimestre.",

    "Copie qui témoigne d'un manque de préparation important. Le sujet est "
    "abordé de façon très superficielle et une bonne partie du devoir "
    "s'éloigne de la question posée, ce qui constitue un hors-sujet "
    "partiel préjudiciable à la note globale. La méthode de l'exercice "
    "n'est manifestement pas maîtrisée : absence de problématique claire, "
    "plan bancal, paragraphes qui ne développent pas d'idée précise. Les "
    "rares références au texte sont approximatives et laissent penser que "
    "la lecture de l'œuvre n'a pas été faite avec suffisamment "
    "d'attention. Le niveau de langue est également très en deçà de ce "
    "qui est attendu à ce niveau scolaire : phrases très courtes et "
    "juxtaposées, vocabulaire limité, nombreuses fautes qui rendent "
    "certains passages difficiles à comprendre. Je comprends que "
    "l'exercice reste difficile, mais un minimum de travail personnel "
    "(relecture du cours, entraînement régulier à la rédaction) est "
    "indispensable pour progresser. Je vous invite vivement à reprendre "
    "les fiches méthode distribuées en début d'année et à les utiliser "
    "systématiquement comme grille de relecture avant de rendre un "
    "devoir. Un rendez-vous en aide personnalisée serait également "
    "bénéfique pour retravailler les bases de l'analyse littéraire. Il "
    "n'est pas trop tard pour rattraper ce retard, mais cela demandera un "
    "investissement plus régulier dans les semaines à venir, notamment en "
    "reprenant chaque soir quelques lignes du cours pour consolider les "
    "bases. Je reste disponible pour vous accompagner dans cette "
    "progression.",

    "Devoir en grande difficulté qui nécessite un accompagnement "
    "rapproché. La consigne semble avoir été mal comprise dès le départ, "
    "ce qui explique le décalage important entre ce qui était demandé et "
    "ce qui est produit. Il n'y a pas de véritable introduction ni de "
    "conclusion identifiables, et le corps du devoir se limite à quelques "
    "remarques éparses sans organisation d'ensemble. Le texte source est "
    "à peine mobilisé, ce qui suggère un manque de lecture préalable ou "
    "une grande difficulté à s'appuyer sur lui pour construire une "
    "analyse. Le vocabulaire employé reste très pauvre et de nombreuses "
    "phrases sont incomplètes ou incorrectes sur le plan grammatical, ce "
    "qui gêne considérablement la compréhension. Il est essentiel de "
    "reprendre les bases de la méthode depuis le début : qu'est-ce qu'une "
    "problématique, comment construire un paragraphe argumenté, comment "
    "analyser une citation. Je vous propose de reprendre ensemble, lors "
    "d'une séance d'aide personnalisée, un exemple de devoir bien "
    "construit afin d'en identifier la structure pas à pas. Il serait "
    "également utile de vous constituer un lexique d'analyse littéraire à "
    "réviser régulièrement, avec des verbes d'analyse variés et leur "
    "usage correct. Un travail régulier sur la lecture à voix haute "
    "pourrait également vous aider à mieux percevoir le rythme et la "
    "musicalité des textes étudiés. Ne vous découragez pas : ces "
    "difficultés sont identifiées et un travail méthodique, même modeste "
    "mais régulier, permettra une progression sensible d'ici la fin de "
    "l'année scolaire. "
    "Je reste à votre disposition pour en discuter.",
]


def note_et_appreciation(rng):
    if rng.random() < 0.08:
        return None, None
    valeur = round(rng.triangular(20 * 0.35, 20, 20 * 0.75), 1)
    ratio = valeur / 20
    if ratio >= 0.7:
        appreciation = rng.choice(APPRECIATIONS_BONNES)
    elif ratio >= 0.5:
        appreciation = rng.choice(APPRECIATIONS_MOYENNES)
    else:
        appreciation = rng.choice(APPRECIATIONS_FAIBLES)
    return valeur, appreciation


def main():
    passphrase = sys.argv[1] if len(sys.argv) > 1 else PASSPHRASE_DEFAULT

    if store.is_initialized():
        print(f"Une base existe déjà dans {store.DATA_DIR} — annulé.")
        print("Arrêtez l'application puis supprimez data/ si vous voulez repartir de zéro.")
        return 1

    rng = random.Random(42)
    store.create_new(passphrase)
    conn = store.get_conn()

    cur = conn.execute("INSERT INTO annee_scolaire (libelle) VALUES (?)", ("2025-2026",))
    annee_id = cur.lastrowid

    for nom_classe, eleves in CLASSES.items():
        cur = conn.execute(
            "INSERT INTO classe (annee_scolaire_id, nom, systeme_periode) VALUES (?, ?, ?)",
            (annee_id, nom_classe, SYSTEME_PAR_CLASSE[nom_classe]),
        )
        classe_id = cur.lastrowid

        eleve_ids = []
        for nom, prenom in eleves:
            cur = conn.execute(
                "INSERT INTO eleve (classe_id, nom, prenom) VALUES (?, ?, ?)",
                (classe_id, nom, prenom),
            )
            eleve_ids.append(cur.lastrowid)

        for titre, date_devoir, coefficient, periode in DEVOIRS_PAR_CLASSE[nom_classe]:
            cur = conn.execute(
                "INSERT INTO devoir (classe_id, titre, date_devoir, coefficient, periode) VALUES (?, ?, ?, ?, ?)",
                (classe_id, titre, date_devoir, coefficient, periode),
            )
            devoir_id = cur.lastrowid

            for eleve_id in eleve_ids:
                valeur, appreciation = note_et_appreciation(rng)
                conn.execute(
                    "INSERT INTO note (devoir_id, eleve_id, valeur, appreciation) VALUES (?, ?, ?, ?)",
                    (devoir_id, eleve_id, valeur, appreciation),
                )

    conn.commit()
    store.save()

    print("Jeu de données factices créé avec succès.")
    print(f"  Mot de passe : {passphrase}")
    print(f"  Année : 2025-2026 — Classes : {', '.join(CLASSES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
