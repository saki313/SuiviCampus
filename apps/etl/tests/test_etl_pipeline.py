"""Tests du pipeline ETL complet (Phase 13).

Vérifie que le pipeline charge correctement les données du mock dans
l'OLTP et le Data Warehouse (schéma en étoile).
"""
import pytest

from apps.etl.clients.mock import MockCampusFasoClient
from apps.etl.services.pipeline import EtlPipeline, executer_etl
from apps.etl.models import EtlRun, EtlCheckpoint
from apps.accounts.models import ProfilEtudiant
from apps.academics.models import UniteEnseignement, ResultatAcademique, Presence
from apps.warehouse.models import (
    DimEtudiant, DimUE, DimSemestre, DimTemps, FaitResultats,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def petit_mock():
    """Mock avec seulement 5 étudiants pour des tests rapides."""
    return MockCampusFasoClient(nb_etudiants=5, graine=42)


class TestPipelineChargement:
    """Tests du chargement OLTP + DW."""

    def test_run_cree_entree_etlrun(self, petit_mock):
        """Le pipeline doit créer une entrée EtlRun en base."""
        pipeline = EtlPipeline(client=petit_mock)
        run = pipeline.executer(differentiel=False)
        assert run.id is not None
        assert run.statut == EtlRun.Statut.SUCCES
        assert run.date_fin is not None

    def test_chargement_ues(self, petit_mock):
        """Le pipeline doit charger les 12 UE."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        assert UniteEnseignement.objects.count() == 12

    def test_chargement_etudiants(self, petit_mock):
        """Le pipeline doit charger les 5 étudiants."""
        pipeline = EtlPipeline(client=petit_mock)
        run = pipeline.executer(differentiel=False)
        assert ProfilEtudiant.objects.count() == 5
        assert run.nb_etudiants_charges == 5

    def test_chargement_resultats(self, petit_mock):
        """Le pipeline doit charger les résultats académiques."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        assert ResultatAcademique.objects.count() > 0

    def test_chargement_presences(self, petit_mock):
        """Le pipeline doit charger les présences."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        assert Presence.objects.count() > 0


class TestChargementDataWarehouse:
    """Tests du chargement du schéma en étoile."""

    def test_dim_etudiant_alimentee(self, petit_mock):
        """DimEtudiant doit être alimentée."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        assert DimEtudiant.objects.count() == 5

    def test_dim_ue_alimentee(self, petit_mock):
        """DimUE doit être alimentée."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        assert DimUE.objects.count() == 12

    def test_fait_resultats_alimente(self, petit_mock):
        """FaitResultats doit être alimentée."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        assert FaitResultats.objects.count() > 0

    def test_dim_semestre_alimentee(self, petit_mock):
        """DimSemestre doit être alimentée."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        assert DimSemestre.objects.count() > 0


class TestIdempotenceEtDifferential:
    """Tests de l'idempotence et de la synchro différentielle."""

    def test_idempotence_double_run(self, petit_mock):
        """Un second run ne doit pas dupliquer les données."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=False)
        count_apres_1 = ProfilEtudiant.objects.count()

        pipeline2 = EtlPipeline(client=petit_mock)
        pipeline2.executer(differentiel=False)
        count_apres_2 = ProfilEtudiant.objects.count()

        assert count_apres_1 == count_apres_2 == 5

    def test_checkpoints_mis_a_jour(self, petit_mock):
        """Les checkpoints doivent être mis à jour après un run différentiel."""
        pipeline = EtlPipeline(client=petit_mock)
        pipeline.executer(differentiel=True)
        # Les checkpoints pour etudiants et resultats doivent exister
        cp_etu = EtlCheckpoint.objects.filter(ressource="etudiants").first()
        assert cp_etu is not None
        assert cp_etu.derniere_synchro is not None


class TestEntreeFonctionnelle:
    """Test de la fonction d'entrée executer_etl."""

    def test_executer_etl_retourne_run(self, petit_mock, monkeypatch):
        """executer_etl doit retourner un EtlRun en succès."""
        # Monkeypatch get_client pour utiliser notre petit mock
        import apps.etl.clients as clients_mod
        monkeypatch.setattr(
            clients_mod, "get_client", lambda: petit_mock
        )
        run = executer_etl(differentiel=False)
        assert isinstance(run, EtlRun)
        assert run.statut == EtlRun.Statut.SUCCES
