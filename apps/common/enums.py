"""Énumérations métier partagées (choices Django).

Définies ici pour être réutilisées par plusieurs applications sans
créer de dépendances circulaires.
"""
from django.db import models


class NiveauRisque(models.TextChoices):
    """Classification du score de risque (Eq 2.1, mémoire §2.4.3)."""
    FAIBLE = "Faible", "Faible (≤ 30)"
    MODERE = "Modere", "Modéré (31–60)"
    ELEVE = "Eleve", "Élevé (> 60)"


class StatutAlerte(models.TextChoices):
    """Cycle de vie d'une alerte (mémoire §A.1)."""
    ACTIVE = "Active", "Active"
    TRAITEE = "Traitee", "Traitée"
    ARCHIVEE = "Archivee", "Archivée"


class TypeAlerte(models.TextChoices):
    """Types d'alerte académique (mémoire §A.1)."""
    ECHEC_UE = "echec_ue", "Échec UE"
    ABSENCE = "absence", "Absence"
    CREDITS = "credits", "Crédits insuffisants"
    RISQUE = "risque", "Risque global"


class NiveauLMD(models.TextChoices):
    """Niveaux Licence-Master-Doctorat (mémoire §A.1)."""
    L1 = "L1", "Licence 1"
    L2 = "L2", "Licence 2"
    L3 = "L3", "Licence 3"
    M1 = "M1", "Master 1"
    M2 = "M2", "Master 2"


class SessionExamen(models.TextChoices):
    """Sessions d'examen (mémoire schéma DW, Fig 2.8)."""
    NORMALE = "normale", "Session normale"
    RATTRAPAGE = "rattrapage", "Session de rattrapage"
