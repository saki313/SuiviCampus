"""Calcul du score de risque académique — Eq 2.1 exacte (mémoire §2.4.3).

ScoreRisque = 0,40 × N + 0,30 × C + 0,20 × U + 0,10 × A

où :
    N = (1 − m̄/20) × 100          indicateur notes (m̄ = moyenne générale)
    C = (1 − c_acq/c_total) × 100  indicateur crédits
    U = (u_echec/u_total) × 100    proportion UE en échec
    A = (1 − s_pres/s_tot) × 100   taux d'absentéisme

Bornage : chaque indicateur ∈ [0; 100], Σcoeff = 1 ⇒ ScoreRisque ∈ [0; 100].
Classification : Faible ≤ 30, Modéré 31–60, Élevé > 60.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


class IndicateursRisque(NamedTuple):
    """Les 4 composantes normalisées [0; 100] du score de risque."""

    notes: float          # N : indicateur notes
    credits: float        # C : indicateur crédits
    ue_echec: float       # U : proportion UE en échec
    absenteisme: float    # A : taux d'absentéisme


class Ponderations(NamedTuple):
    """Pondérations des composantes du score (Eq 2.1)."""

    notes: float = 0.40
    credits: float = 0.30
    ue_echec: float = 0.20
    absenteisme: float = 0.10


# Pondérations par défaut (exactement celles du mémoire)
PONDERATIONS_DEFAUT = Ponderations()


@dataclass(frozen=True)
class ResultatRisque:
    """Résultat complet du calcul de score de risque."""

    score: float
    indicateurs: IndicateursRisque
    classification: str  # "Faible" | "Modere" | "Eleve"


def _clamp(valeur: float) -> float:
    """Ramène une valeur dans [0; 100]."""
    return max(0.0, min(100.0, valeur))


def indicateur_notes(moyenne_generale: float) -> float:
    """N = (1 − m̄/20) × 100.

    Args:
        moyenne_generale: m̄ ∈ [0; 20]. Si None ou hors bornes, clampé.
    """
    if moyenne_generale is None:
        return 0.0
    moyenne = max(0.0, min(20.0, moyenne_generale))
    return _clamp((1.0 - moyenne / 20.0) * 100.0)


def indicateur_credits(credits_acquis: int, credits_total: int) -> float:
    """C = (1 − c_acq / c_total) × 100.

    Plus on a de crédits acquis, plus C est faible (moins de risque).
    """
    if not credits_total or credits_total <= 0:
        return 0.0
    return _clamp((1.0 - credits_acquis / credits_total) * 100.0)


def indicateur_ue_echec(ues_echec: int, ues_total: int) -> float:
    """U = (u_echec / u_total) × 100.

    Plus on a d'UE en échec, plus U est élevé (plus de risque).
    """
    if not ues_total or ues_total <= 0:
        return 0.0
    return _clamp((ues_echec / ues_total) * 100.0)


def indicateur_absenteisme(sessions_presentes: int, sessions_total: int) -> float:
    """A = (1 − s_pres / s_tot) × 100.

    Plus on est absent, plus A est élevé (plus de risque).
    """
    if not sessions_total or sessions_total <= 0:
        return 0.0
    return _clamp((1.0 - sessions_presentes / sessions_total) * 100.0)


def calculer_indicateurs(
    moyenne_generale: float | None = None,
    credits_acquis: int = 0,
    credits_total: int = 0,
    ues_echec: int = 0,
    ues_total: int = 0,
    sessions_presentes: int = 0,
    sessions_total: int = 0,
) -> IndicateursRisque:
    """Calcule les 4 indicateurs normalisés [0; 100]."""
    return IndicateursRisque(
        notes=indicateur_notes(moyenne_generale),
        credits=indicateur_credits(credits_acquis, credits_total),
        ue_echec=indicateur_ue_echec(ues_echec, ues_total),
        absenteisme=indicateur_absenteisme(sessions_presentes, sessions_total),
    )


def calculer_score(
    indicateurs: IndicateursRisque,
    ponderations: Ponderations = PONDERATIONS_DEFAUT,
) -> float:
    """ScoreRisque = 0,40×N + 0,30×C + 0,20×U + 0,10×A.

    Borné dans [0; 100] par construction (chaque indicateur ∈ [0;100], Σcoeff=1).
    """
    score = (
        ponderations.notes * indicateurs.notes
        + ponderations.credits * indicateurs.credits
        + ponderations.ue_echec * indicateurs.ue_echec
        + ponderations.absenteisme * indicateurs.absenteisme
    )
    return _clamp(score)


def classifier_score(score: float) -> str:
    """Classification du score : Faible ≤ 30, Modéré 31–60, Élevé > 60."""
    if score <= 30:
        return "Faible"
    elif score <= 60:
        return "Modere"
    else:
        return "Eleve"


def calculer_score_complet(
    moyenne_generale: float | None = None,
    credits_acquis: int = 0,
    credits_total: int = 0,
    ues_echec: int = 0,
    ues_total: int = 0,
    sessions_presentes: int = 0,
    sessions_total: int = 0,
    ponderations: Ponderations = PONDERATIONS_DEFAUT,
) -> ResultatRisque:
    """Pipeline complet : indicateurs → score → classification."""
    ind = calculer_indicateurs(
        moyenne_generale, credits_acquis, credits_total,
        ues_echec, ues_total, sessions_presentes, sessions_total,
    )
    score = calculer_score(ind, ponderations)
    return ResultatRisque(
        score=score,
        indicateurs=ind,
        classification=classifier_score(score),
    )
