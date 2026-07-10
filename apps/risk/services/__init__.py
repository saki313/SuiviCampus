"""Service Score de Risque (BF02) — wrapper de la couche domain pour l'UI/API.

Fournit une API simple au reste de l'application (vues, serializers, scheduler) :
  - get_score_etudiant(etudiant)        → dict lisible (score, niveau, indicateurs)
  - get_scores_promotion(filtres)       → QuerySet pour tableaux de bord
  - get_ue_critiques(...)               → BF10 : UE les plus difficiles

Toute la logique métier reste dans domain/ ; ce service ne fait que
l'adapter aux objets Django.
"""
from __future__ import annotations

from typing import Optional

from django.db.models import Avg, Count, Q

from apps.accounts.models import ProfilEtudiant
from apps.academics.models import ResultatAcademique, UniteEnseignement
from apps.analytics.models import IndicateurAcademique
from apps.analytics.services import calculer_indicateurs_etudiant
from domain.kpi.score_risque import (
    Ponderations,
    ResultatRisque,
    calculer_score_complet,
)


def get_score_etudiant(etudiant: ProfilEtudiant) -> dict:
    """Retourne le score de risque d'un étudiant sous forme lisible.

    Recalcule si nécessaire (l'indicateur persisté peut être absent avant
    le passage du scheduler KPI).
    """
    try:
        indic = IndicateurAcademique.objects.get(etudiant=etudiant, semestre=None)
    except IndicateurAcademique.DoesNotExist:
        indic = calculer_indicateurs_etudiant(etudiant)
    return {
        "etudiant_id": etudiant.id,
        "matricule": etudiant.matricule,
        "score": indic.score_risque,
        "niveau": indic.classification_risque,
        "indicateurs": {
            "moyenne_generale": float(indic.moyenne_generale) if indic.moyenne_generale else None,
            "taux_progression": indic.taux_progression,
            "taux_absenteisme": indic.taux_absenteisme,
            "credits_acquis": indic.credits_acquis,
            "credits_total": indic.credits_total,
        },
    }


def get_scores_promotion(
    filiere: Optional[str] = None,
    niveau: Optional[str] = None,
):
    """QuerySet d'indicateurs pour une promotion filtrée (BF03, BF09)."""
    qs = IndicateurAcademique.objects.filter(semestre=None).select_related(
        "etudiant", "etudiant__utilisateur"
    )
    if filiere:
        qs = qs.filter(etudiant__filiere=filiere)
    if niveau:
        qs = qs.filter(etudiant__niveau=niveau)
    return qs


def get_distribution_scores(filiere=None, niveau=None) -> dict:
    """Distribution des étudiants par niveau de risque (BF03 TB Responsable)."""
    qs = get_scores_promotion(filiere, niveau)
    distribution = qs.values("classification_risque").annotate(
        effectif=Count("id")
    )
    result = {"Faible": 0, "Modere": 0, "Eleve": 0}
    for row in distribution:
        key = row["classification_risque"]
        if key in result:
            result[key] = row["effectif"]
    return result


def get_ue_critiques(filiere=None, niveau=None, limite: int = 10) -> list[dict]:
    """BF10 : identifie les UE présentant les plus fortes difficultés.

    Critère : taux d'échec le plus élevé (note < 10/20 ou valide=False).
    """
    qs = ResultatAcademique.objects.all()
    if filiere or niveau:
        qs = qs.filter(
            Q(etudiant__filiere=filiere) if filiere else Q(),
            Q(etudiant__niveau=niveau) if niveau else Q(),
        )

    stats = qs.values("ue__code", "ue__intitule", "ue__credits").annotate(
        total=Count("id"),
        echecs=Count("id", filter=Q(valide=False)),
        moyenne=Avg("note"),
    ).order_by("-echecs")[:limite]

    return [
        {
            "code": row["ue__code"],
            "intitule": row["ue__intitule"],
            "credits": row["ue__credits"],
            "effectif": row["total"],
            "echecs": row["echecs"],
            "taux_echec": round((row["echecs"] / row["total"]) * 100, 1) if row["total"] else 0,
            "moyenne": round(float(row["moyenne"]), 2) if row["moyenne"] else None,
        }
        for row in stats
    ]
