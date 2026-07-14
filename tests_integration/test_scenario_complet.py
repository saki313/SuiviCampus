"""Tests d'intégration — scénario complet DS1/DS2/DS3 (Phase 14).

Vérifie le flux critique end-to-end :
  DS3 — ETL : extraction mock → chargement OLTP + DW
  DS1 — Calcul KPI : agrégation → score risque (Eq 2.1) → progression (Eq 2.2)
  DS2 — Alertes : seuils → génération → recommandations
  Sortie — Dashboards + Rapports fonctionnels

Ce test valide que toutes les couches communiquent correctement.
"""
import pytest

from apps.etl.clients.mock import MockCampusFasoClient, CATALOGUE_UE
from apps.etl.services.pipeline import EtlPipeline
from apps.etl.models import EtlRun
from apps.accounts.models import ProfilEtudiant
from apps.academics.models import UniteEnseignement, ResultatAcademique, Presence
from apps.warehouse.models import DimEtudiant, DimUE, DimSemestre, FaitResultats
from apps.analytics.models import IndicateurAcademique
from apps.analytics.services import calculer_indicateurs_promotion
from apps.alerts.models import Alerte, ParametreAlerte, Recommandation
from apps.alerts.services import verifier_promotion


pytestmark = [pytest.mark.django_db, pytest.mark.slow]


@pytest.fixture
def petit_mock():
    return MockCampusFasoClient(nb_etudiants=15, graine=42)


class TestScenarioComplet:
    """Scénario d'intégration DS3 → DS1 → DS2."""

    def test_ds3_etl_charge_donnees(self, petit_mock):
        """DS3 : L'ETL charge les données dans l'OLTP et le DW."""
        pipeline = EtlPipeline(client=petit_mock)
        run = pipeline.executer(differentiel=False)

        # OLTP
        assert ProfilEtudiant.objects.count() == 15
        assert UniteEnseignement.objects.count() == len(CATALOGUE_UE)
        assert ResultatAcademique.objects.count() > 0
        assert Presence.objects.count() > 0

        # DW (schéma en étoile)
        assert DimEtudiant.objects.count() == 15
        assert DimUE.objects.count() == len(CATALOGUE_UE)
        assert DimSemestre.objects.count() > 0
        assert FaitResultats.objects.count() > 0

        # EtlRun
        assert run.statut == EtlRun.Statut.SUCCES
        assert run.nb_etudiants_charges == 15

    def test_ds1_calcul_kpi_apres_etl(self, petit_mock):
        """DS1 : Le calcul KPI produit des indicateurs pour chaque étudiant.

        Le score de risque (Eq 2.1) et la progression (Eq 2.2) doivent
        être calculés et persistés dans IndicateurAcademique.
        """
        # Étape 1 : ETL
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)

        # Étape 2 : Calcul KPI
        count = calculer_indicateurs_promotion()
        assert count == 15
        assert IndicateurAcademique.objects.filter(semestre=None).count() == 15

        # Vérifications des formules
        for indic in IndicateurAcademique.objects.filter(semestre=None):
            # Score ∈ [0, 100]
            assert indic.score_risque is not None
            assert 0 <= indic.score_risque <= 100
            # Classification cohérente
            if indic.score_risque <= 30:
                assert indic.classification_risque == "Faible"
            elif indic.score_risque <= 60:
                assert indic.classification_risque == "Modere"
            else:
                assert indic.classification_risque == "Eleve"
            # Progression ∈ [0, 100]
            assert indic.taux_progression is not None
            assert 0 <= indic.taux_progression <= 100

    def test_ds2_alertes_generees_apres_kpi(self, petit_mock):
        """DS2 : Les alertes sont générées pour les étudiants à risque.

        Le gestionnaire d'alertes doit :
          - créer des alertes pour les scores > seuil
          - créer des recommandations associées
          - ne pas dupliquer les alertes existantes
        """
        # Étape 1 : ETL
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)

        # Étape 2 : KPI
        calculer_indicateurs_promotion()

        # Étape 3 : Alertes
        nb_alertes = verifier_promotion()
        assert nb_alertes > 0

        # Vérifier les alertes créées
        alertes = Alerte.objects.all()
        assert alertes.count() > 0

        # Chaque alerte doit avoir au moins une recommandation
        for alerte in alertes[:10]:
            assert alerte.recommandations.count() >= 1

        # Distribution non vide : au moins un étudiant par catégorie de risque
        indic_eleves = IndicateurAcademique.objects.filter(
            classification_risque="Eleve", semestre=None
        ).count()
        assert indic_eleves > 0, "Au moins un étudiant doit être à risque élevé"

    def test_rapports_fonctionnels_apres_scenario(self, petit_mock):
        """Les rapports doivent se générer sans erreur après le scénario."""
        from apps.reporting.services.pdf_export import exporter_pdf
        from apps.reporting.services.excel_export import exporter_excel
        from apps.reporting.services.csv_export import exporter_csv

        # ETL + KPI + Alertes
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        calculer_indicateurs_promotion()
        verifier_promotion()

        # PDF
        pdf = exporter_pdf()
        assert pdf.getvalue()[:5] == b"%PDF-"
        assert len(pdf.getvalue()) > 2000

        # Excel
        xlsx = exporter_excel()
        assert xlsx.getvalue()[:4] == b"PK\x03\x04"

        # CSV
        csv_buf = exporter_csv()
        lines = csv_buf.getvalue().strip().split("\n")
        assert len(lines) >= 16  # en-tête + 15 étudiants

    def test_formule_equation_21_bornage(self, petit_mock):
        """Vérifie que le score Eq 2.1 est bien borné [0; 100] pour tous."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        calculer_indicateurs_promotion()

        for indic in IndicateurAcademique.objects.filter(semestre=None):
            assert 0 <= indic.score_risque <= 100, (
                f"Score hors bornes pour {indic.etudiant.matricule}: "
                f"{indic.score_risque}"
            )

    def test_double_alerte_non_dupliquee(self, petit_mock):
        """Un second passage de vérification ne crée pas de doublons."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        calculer_indicateurs_promotion()

        nb1 = verifier_promotion()
        nb2 = verifier_promotion()
        assert nb2 == 0, "Le second passage ne doit générer aucune alerte"
