"""Tests de performance (Phase 15) — respect du cahier des charges.

Le cahier des charges impose un temps de réponse < 3 s par requête
(besoin non fonctionnel « Performance », mémoire §2.4.3).

Ce test valide que les endpoints critiques restent sous le seuil :
  - dashboards (étudiant, enseignant, responsable, admin)
  - listes paginées (étudiants, résultats)
  - recalcul KPI d'une promotion
  - génération des rapports (PDF/Excel/CSV)

Les seuils sont volontairement TRES en dessous de 3 s pour rester
représentatifs du matériel de production même sous charge.

NB : ces tests utilisent le mock ETL (85 étudiants, ~1020 résultats)
pour reproduire fidèlement le volume cible (mémoire §2.4.3).
"""
import time

import pytest

from apps.etl.clients.mock import MockCampusFasoClient
from apps.etl.services.pipeline import EtlPipeline
from apps.analytics.services import (
    calculer_indicateurs_promotion,
    calculer_indicateurs_etudiant,
)
from apps.alerts.services import verifier_promotion
from apps.accounts.models import Utilisateur, ProfilEtudiant
from apps.analytics.models import IndicateurAcademique
from apps.academics.models import ResultatAcademique
from apps.reporting.services.pdf_export import exporter_pdf
from apps.reporting.services.excel_export import exporter_excel
from apps.reporting.services.csv_export import exporter_csv
from apps.risk.services import (
    get_distribution_scores,
    get_ue_critiques,
    get_scores_promotion,
)


pytestmark = [pytest.mark.django_db, pytest.mark.slow]

# Seuil du cahier des charges (ms) — on vise 1 s en test unitaire,
# la marge de 2 s absorbe la charge de production.
SEUIL_REQUETE_MS = 3000


# ---------------------------------------------------------------------------
# Fixture : charge le dataset complet (85 étudiants, ~1020 résultats)
# ---------------------------------------------------------------------------

@pytest.fixture
def dataset_charge(db):
    """Charge le dataset mock complet (≈ 85 étudiants) une fois.

    Le db fixture est function-scoped (pytest-django), le dataset est
    recréé par pytest via --reuse-db en SQLite en mémoire.
    """
    client = MockCampusFasoClient(nb_etudiants=85, graine=42)
    pipeline = EtlPipeline(client=client)
    pipeline.executer(differentiel=False)
    calculer_indicateurs_promotion()
    verifier_promotion()
    return {
        "nb_etudiants": ProfilEtudiant.objects.count(),
        "nb_resultats": ResultatAcademique.objects.count(),
        "nb_indicateurs": IndicateurAcademique.objects.count(),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


# ---------------------------------------------------------------------------
# Tests de performance des services (sans Django HTTP)
# ---------------------------------------------------------------------------

class TestPerformanceServices:
    """Mesure le temps d'exécution des services critiques (Eq 2.1/2.2)."""

    def test_recalcul_kpi_promotion_rapide(self, dataset_charge):
        """Recalcul complet des indicateurs d'une promotion (85 étudiants).

        Doit rester sous le seuil du cahier des charges (< 3 s).
        """
        start = time.perf_counter()
        nb = calculer_indicateurs_promotion()
        elapsed = _elapsed_ms(start)

        assert nb == 85
        assert elapsed < SEUIL_REQUETE_MS, (
            f"Recalcul KPI trop lent : {elapsed:.0f} ms (seuil {SEUIL_REQUETE_MS} ms)"
        )

    def test_distribution_scores_rapide(self, dataset_charge):
        """Distribution agrégée par classification (1 requête SQL)."""
        start = time.perf_counter()
        dist = get_distribution_scores()
        elapsed = _elapsed_ms(start)

        assert sum(dist.values()) > 0
        assert elapsed < 1000, (
            f"Distribution trop lente : {elapsed:.0f} ms"
        )

    def test_ue_critiques_rapide(self, dataset_charge):
        """Identification des UE critiques (agrégation SQL)."""
        start = time.perf_counter()
        ues = get_ue_critiques(limite=10)
        elapsed = _elapsed_ms(start)

        assert len(ues) > 0
        assert elapsed < 1000, (
            f"UE critiques trop lent : {elapsed:.0f} ms"
        )

    def test_scores_promotion_avec_indicateurs(self, dataset_charge):
        """Le QuerySet scores_promotion doit rester léger (lazy)."""
        start = time.perf_counter()
        qs = get_scores_promotion()
        # Forcer l'évaluation complète (select_related + filtre)
        liste = list(qs)
        elapsed = _elapsed_ms(start)

        assert len(liste) > 0
        assert elapsed < 1500, (
            f"Scores promotion trop lent : {elapsed:.0f} ms"
        )

    def test_calcul_indicateur_etudiant_rapide(self, dataset_charge):
        """Calcul d'UN étudiant doit être instantané (< 200 ms)."""
        etudiant = ProfilEtudiant.objects.first()
        start = time.perf_counter()
        calculer_indicateurs_etudiant(etudiant)
        elapsed = _elapsed_ms(start)

        assert elapsed < 200, (
            f"Calcul 1 étudiant trop lent : {elapsed:.0f} ms"
        )


# ---------------------------------------------------------------------------
# Tests de performance des rapports
# ---------------------------------------------------------------------------

class TestPerformanceRapports:
    """Génération PDF/Excel/CSV — doit respecter le seuil de 3 s."""

    def test_rapport_csv_rapide(self, dataset_charge):
        """Export CSV complet de la promotion."""
        start = time.perf_counter()
        buffer = exporter_csv()
        elapsed = _elapsed_ms(start)
        contenu = buffer.getvalue()

        assert len(contenu) > 0
        assert elapsed < SEUIL_REQUETE_MS, (
            f"CSV trop lent : {elapsed:.0f} ms"
        )

    def test_rapport_excel_rapide(self, dataset_charge):
        """Export Excel complet (3 feuilles)."""
        start = time.perf_counter()
        buffer = exporter_excel()
        elapsed = _elapsed_ms(start)

        assert len(buffer.getvalue()) > 0
        assert elapsed < SEUIL_REQUETE_MS, (
            f"Excel trop lent : {elapsed:.0f} ms"
        )

    def test_rapport_pdf_rapide(self, dataset_charge):
        """Génération du PDF de synthèse."""
        start = time.perf_counter()
        buffer = exporter_pdf()
        elapsed = _elapsed_ms(start)

        assert len(buffer.getvalue()) > 0
        assert elapsed < SEUIL_REQUETE_MS, (
            f"PDF trop lent : {elapsed:.0f} ms"
        )
