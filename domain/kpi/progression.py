"""Calcul de progression et projection de diplomation — Eq 2.2 (mémoire §2.4.3).

TauxProgression = (c_acq / c_total) × 100  [%]

SemestresRestants = (c_total − c_acq) / c̄_sem

c̄_sem = nombre moyen de crédits validés par semestre, calculé à partir
de l'historique réel de l'étudiant (pas un idéal théorique).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class ResultatProgression:
    """Résultat complet du calcul de progression."""

    taux_progression: float       # [%] ∈ [0; 100]
    credits_acquis: int
    credits_total: int
    credits_moyen_par_semestre: float  # c̄_sem
    semestres_restants: float     # peut être un décimal
    projection_diplomation: date | None


def calculer_taux_progression(credits_acquis: int, credits_total: int) -> float:
    """TauxProgression = (c_acq / c_total) × 100."""
    if not credits_total or credits_total <= 0:
        return 0.0
    return min(100.0, (credits_acquis / credits_total) * 100.0)


def calculer_semestres_restants(
    credits_acquis: int,
    credits_total: int,
    credits_moyen_par_semestre: float,
) -> float:
    """SemestresRestants = (c_total − c_acq) / c̄_sem.

    Si c̄_sem <= 0 ou credits_acquis >= credits_total, retourne 0.
    """
    if credits_moyen_par_semestre <= 0 or credits_acquis >= credits_total:
        return 0.0
    return (credits_total - credits_acquis) / credits_moyen_par_semestre


def calculer_credits_moyen_par_semestre(
    credits_acquis: int,
    semestres_valides: int,
) -> float:
    """c̄_sem : moyenne réelle de crédits validés par semestre.

    Si aucun semestre validé, retourne 0 pour éviter une division par zéro.
    """
    if not semestres_valides or semestres_valides <= 0:
        return 0.0
    return credits_acquis / semestres_valides


def calculer_projection_diplomation(
    semestres_restants: float,
    date_reference: date | None = None,
) -> date | None:
    """Estime la date de diplomation à partir du nombre de semestres restants.

    Hypothèse : un semestre ≈ 6 mois calendaire.
    Si semestres_restants = 0, retourne la date de référence.
    """
    if semestres_restants <= 0:
        return date_reference
    ref = date_reference or date.today()
    # 1 semestre ≈ 6 mois, arrondi au mois supérieur pour sécurité
    jours_par_semestre = 183  # ~6 mois
    delta = timedelta(days=int(semestres_restants * jours_par_semestre))
    return ref + delta


def calculer_progression_complet(
    credits_acquis: int,
    credits_total: int,
    semestres_valides: int,
    date_reference: date | None = None,
) -> ResultatProgression:
    """Pipeline complet : taux → c̄_sem → semestres restants → projection."""
    taux = calculer_taux_progression(credits_acquis, credits_total)
    c_barre = calculer_credits_moyen_par_semestre(credits_acquis, semestres_valides)
    sem_rest = calculer_semestres_restants(credits_acquis, credits_total, c_barre)
    proj = calculer_projection_diplomation(sem_rest, date_reference)
    return ResultatProgression(
        taux_progression=taux,
        credits_acquis=credits_acquis,
        credits_total=credits_total,
        credits_moyen_par_semestre=c_barre,
        semestres_restants=sem_rest,
        projection_diplomation=proj,
    )
