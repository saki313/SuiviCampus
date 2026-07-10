"""Seuils et classification du score de risque (mémoire §2.4.3).

Les seuils sont calibrables via ParametreAlerte (D6). Ce module fournit
les valeurs par défaut et les fonctions de classification.
"""

# Seuils par défaut (identiques à ParametreAlerte par défaut)
SEUIL_FAIBLE = 30.0    # Score <= 30 → Faible
SEUIL_MODERE = 60.0    # Score <= 60 → Modéré ; > 60 → Élevé


def classifier(score: float, seuil_faible: float = SEUIL_FAIBLE, seuil_modere: float = SEUIL_MODERE) -> str:
    """Classifie un score en 3 niveaux."""
    if score <= seuil_faible:
        return "Faible"
    elif score <= seuil_modere:
        return "Modere"
    else:
        return "Eleve"
