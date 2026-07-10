"""Tests du client mock ETL et du pipeline de données (Phase 13).

Tests du MockCampusFasoClient : vérifie la cohérence des données générées
(nombre, format, déterminisme) sans nécessiter de base de données.
"""
import pytest
from unittest.mock import patch

from apps.etl.clients.mock import MockCampusFasoClient
from apps.etl.clients.base import (
    SourceEtudiant, SourceUE, SourceResultat, SourcePresence,
)


class TestMockCampusFasoClient:
    """Tests du générateur de données mock."""

    @pytest.fixture
    def client(self):
        return MockCampusFasoClient(nb_etudiants=10, graine=42)

    def test_extract_ues_nombre(self, client):
        """Le mock doit générer exactement 12 UE."""
        ues = list(client.extract_ues())
        assert len(ues) == 12

    def test_extract_ues_format(self, client):
        """Chaque UE doit avoir les champs requis."""
        for ue in client.extract_ues():
            assert isinstance(ue, SourceUE)
            assert ue.code and len(ue.code) <= 20
            assert ue.intitule
            assert 0 < ue.credits <= 10
            assert ue.semestre_numero in (1, 2)
            assert ue.ue_type in ("obligatoire", "optionnel")

    def test_extract_etudiants_nombre(self, client):
        """Le mock doit générer le nombre demandé d'étudiants."""
        etudiants = list(client.extract_etudiants())
        assert len(etudiants) == 10

    def test_extract_etudiants_format(self, client):
        """Chaque étudiant doit avoir les champs requis."""
        for e in client.extract_etudiants():
            assert isinstance(e, SourceEtudiant)
            assert e.matricule
            assert e.nom
            assert e.prenom
            assert "@" in e.email
            assert e.niveau in ("L1", "L2", "L3", "M1", "M2")
            assert e.annee_scolaire == "2025-2026"

    def test_extract_etudiants_deterministe(self):
        """Deux instances avec la même graine doivent produire les mêmes données."""
        c1 = MockCampusFasoClient(nb_etudiants=5, graine=42)
        c2 = MockCampusFasoClient(nb_etudiants=5, graine=42)
        e1 = [e.matricule for e in c1.extract_etudiants()]
        e2 = [e.matricule for e in c2.extract_etudiants()]
        assert e1 == e2

    def test_extract_resultats_coherence(self, client):
        """Les résultats doivent référencer des étudiants et UE existants."""
        etudiants = list(client.extract_etudiants())
        ues = list(client.extract_ues())
        matricules = {e.matricule for e in etudiants}
        codes_ue = {u.code for u in ues}

        resultats = list(client.extract_resultats())
        assert len(resultats) > 0

        for r in resultats:
            assert isinstance(r, SourceResultat)
            assert r.matricule in matricules, f"Matricule inconnu: {r.matricule}"
            assert r.code_ue in codes_ue, f"UE inconnue: {r.code_ue}"
            assert 0 <= r.note <= 20
            assert r.valide is not None
            assert r.session in ("normale", "rattrapage")

    def test_extract_presences_format(self, client):
        """Les présences doivent avoir le bon format."""
        presences = list(client.extract_presences())
        assert len(presences) > 0
        for p in presences:
            assert isinstance(p, SourcePresence)
            assert p.matricule
            assert p.code_ue
            assert isinstance(p.present, bool)

    def test_health_check(self, client):
        """Le mock doit toujours être disponible."""
        assert client.health_check() is True

    def test_extract_presences_vide_par_defaut(self):
        """Le client abstrait retourne une liste vide par défaut pour les présences."""
        from apps.etl.clients.base import CampusFasoClient

        class MinimalClient(CampusFasoClient):
            def extract_etudiants(self, since=None):
                return []
            def extract_ues(self):
                return []
            def extract_resultats(self, since=None):
                return []

        c = MinimalClient()
        assert list(c.extract_presences()) == []

    def test_taux_reussite_environ_72(self, client):
        """Le mock doit produire environ 72% de réussite globale."""
        resultats = list(client.extract_resultats())
        valides = sum(1 for r in resultats if r.valide)
        taux = valides / len(resultats) * 100
        # Tolérance ±10% (données aléatoires)
        assert 60 <= taux <= 85, f"Taux de réussite {taux:.1f}% hors tolérance"
