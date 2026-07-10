"""Export CSV des indicateurs académiques (BF08).

Génère un fichier CSV contenant les indicateurs par étudiant,
utilisable pour réintégration ou analyse externe.
"""
from __future__ import annotations

import csv
import io
from datetime import date
from typing import Optional

from apps.accounts.models import ProfilEtudiant
from apps.analytics.models import IndicateurAcademique


# En-têtes du CSV
HEADERS = [
    "matricule",
    "nom",
    "prenom",
    "niveau",
    "filiere",
    "promotion",
    "annee_scolaire",
    "moyenne_generale",
    "score_risque",
    "classification_risque",
    "taux_progression",
    "credits_acquis",
    "credits_total",
    "ues_echec",
    "ues_total",
    "taux_absenteisme",
    "semestres_restants",
    "proj_diplomation",
]


def exporter_csv(
    filiere: Optional[str] = None,
    niveau: Optional[str] = None,
) -> io.StringIO:
    """Génère un export CSV des indicateurs académiques.

    Args:
        filiere: filtre par filière (None = toutes).
        niveau: filtre par niveau LMD (None = tous).

    Returns:
        StringIO contenant le CSV (encodage UTF-8).
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(HEADERS)

    qs = _queryset_indicateurs(filiere, niveau)
    for indic in qs:
        etu = indic.etudiant
        user = etu.utilisateur
        writer.writerow([
            etu.matricule,
            user.last_name,
            user.first_name,
            etu.niveau,
            etu.filiere,
            etu.promotion,
            etu.annee_scolaire,
            _fmt(indic.moyenne_generale),
            _fmt(indic.score_risque),
            indic.classification_risque or "",
            _fmt(indic.taux_progression),
            indic.credits_acquis,
            indic.credits_total,
            indic.ues_echec,
            indic.ues_total,
            _fmt(indic.taux_absenteisme),
            _fmt(indic.semestres_restants),
            indic.proj_diplomation.isoformat() if indic.proj_diplomation else "",
        ])

    output.seek(0)
    return output


def _queryset_indicateurs(filiere=None, niveau=None):
    """QuerySet filtré des indicateurs globaux (semestre=None)."""
    qs = IndicateurAcademique.objects.filter(
        semestre=None
    ).select_related("etudiant", "etudiant__utilisateur")
    if filiere:
        qs = qs.filter(etudiant__filiere=filiere)
    if niveau:
        qs = qs.filter(etudiant__niveau=niveau)
    return qs


def _fmt(valeur) -> str:
    """Formate une valeur numérique pour le CSV."""
    if valeur is None:
        return ""
    if isinstance(valeur, float):
        return f"{valeur:.2f}"
    return str(valeur)
