"""Service de calcul des indicateurs académiques (BF02, BF06).

Orchestre : lecture données OLTP → appel domain (Eq 2.1/2.2) → persistance
IndicateurAcademique. Aucune logique métier dans les vues/serializers : tout
passe par ce service.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from django.db.models import Avg, Sum, Count, Q

from apps.academics.models import ResultatAcademique, Presence, HistoriqueAcademique
from apps.accounts.models import ProfilEtudiant
from apps.analytics.models import IndicateurAcademique

# Domaine pur (sans Django)
from domain.kpi.score_risque import (
    calculer_indicateurs,
    calculer_score,
    classifier_score,
    Ponderations,
)
from domain.kpi.progression import calculer_progression_complet


# Crédits totaux visés pour un cycle LMD complet (mémoire, maquettes 90/120)
CREDITS_TOTAL_LICENCE = 180
CREDITS_TOTAL_MASTER = 120


def _credits_total_vises(etudiant: ProfilEtudiant) -> int:
    """Détermine le total de crédits visé selon le niveau LMD."""
    niveau = etudiant.niveau or "L1"
    if niveau.startswith("M"):
        return CREDITS_TOTAL_MASTER
    return CREDITS_TOTAL_LICENCE


def _agreger_resultats(etudiant: ProfilEtudiant) -> dict:
    """Agrège les résultats OLTP de l'étudiant pour le calcul des indicateurs.

    Retourne : moyenne_generale, credits_acquis, credits_total (visés),
    ues_total, ues_echec, sessions_presentes, sessions_total, semestres_valides.
    """
    resultats = ResultatAcademique.objects.filter(etudiant=etudiant)
    agg = resultats.aggregate(
        moyenne=Avg("note"),
        credits=Sum("credits"),
        ues_total=Count("id"),
        ues_echec=Count("id", filter=Q(valide=False)),
    )

    credits_total_vises = _credits_total_vises(etudiant)

    # Présences (indicateur A)
    presences = Presence.objects.filter(etudiant=etudiant)
    pres_agg = presences.aggregate(
        total=Count("id"),
        presentes=Count("id", filter=Q(present=True)),
    )

    # Semestres valides : nb de semestres distincts avec au moins un résultat
    semestres_valides = (
        resultats.values("semestre_id").distinct().count()
    )

    return {
        "moyenne_generale": float(agg["moyenne"]) if agg["moyenne"] is not None else None,
        "credits_acquis": int(agg["credits"] or 0),
        "credits_total": credits_total_vises,
        "ues_total": int(agg["ues_total"] or 0),
        "ues_echec": int(agg["ues_echec"] or 0),
        "sessions_presentes": int(pres_agg["presentes"] or 0),
        "sessions_total": int(pres_agg["total"] or 0),
        "semestres_valides": semestres_valides,
    }


def calculer_indicateurs_etudiant(
    etudiant: ProfilEtudiant,
    ponderations: Optional[Ponderations] = None,
) -> IndicateurAcademique:
    """Calcule et persiste les indicateurs d'un étudiant.

    BF02 (score de risque) + BF06 (progression/projection).
    """
    data = _agreger_resultats(etudiant)
    pond = ponderations or Ponderations()

    # --- Score de risque (Eq 2.1) ---
    indicateurs = calculer_indicateurs(
        moyenne_generale=data["moyenne_generale"],
        credits_acquis=data["credits_acquis"],
        credits_total=data["credits_total"],
        ues_echec=data["ues_echec"],
        ues_total=data["ues_total"],
        sessions_presentes=data["sessions_presentes"],
        sessions_total=data["sessions_total"],
    )
    score = calculer_score(indicateurs, pond)
    classification = classifier_score(score)

    # --- Progression & diplomation (Eq 2.2) ---
    prog = calculer_progression_complet(
        credits_acquis=data["credits_acquis"],
        credits_total=data["credits_total"],
        semestres_valides=data["semestres_valides"],
        date_reference=date.today(),
    )

    # --- Persistance ---
    indicateur, _ = IndicateurAcademique.objects.update_or_create(
        etudiant=etudiant,
        semestre=None,  # agrégat global
        defaults={
            "moyenne_generale": data["moyenne_generale"],
            "score_risque": score,
            "classification_risque": classification,
            "taux_progression": prog.taux_progression,
            "credits_acquis": data["credits_acquis"],
            "credits_total": data["credits_total"],
            "ues_echec": data["ues_echec"],
            "ues_total": data["ues_total"],
            "taux_absenteisme": indicateurs.absenteisme,
            "semestres_restants": prog.semestres_restants,
            "proj_diplomation": prog.projection_diplomation,
        },
    )
    return indicateur


def calculer_indicateurs_promotion(
    etudiants_qs=None,
    ponderations: Optional[Ponderations] = None,
) -> int:
    """Recalcule les indicateurs pour tous les étudiants d'une promotion.

    Retourne le nombre d'étudiants traités. Utilisé par le scheduler KPI
    après chaque synchronisation ETL.
    """
    if etudiants_qs is None:
        etudiants_qs = ProfilEtudiant.objects.all()
    count = 0
    for etudiant in etudiants_qs:
        calculer_indicateurs_etudiant(etudiant, ponderations)
        count += 1
    return count
