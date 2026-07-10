"""Tests du service Risk (wrapper domain pour l'UI/API) — Phase 13.

Vérifie get_score_etudiant, get_distribution_scores, get_ue_critiques.
"""
import pytest

from apps.accounts.models import Utilisateur, ProfilEtudiant
from apps.academics.models import UniteEnseignement, Semestre, ResultatAcademique
from apps.analytics.models import IndicateurAcademique
from apps.risk.services import (
    get_score_etudiant,
    get_distribution_scores,
    get_ue_critiques,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def etudiants_mix(db):
    """Crée 3 étudiants avec classifications différentes."""
    data = []
    for i, (cls, score) in enumerate([
        ("Faible", 15.0), ("Modere", 45.0), ("Eleve", 75.0)
    ]):
        user = Utilisateur.objects.create_user(
            username=f"etu{i}", email=f"etu{i}@test.bf",
            password="TestPass123!", first_name=f"Etu{i}", last_name="T",
            role="etudiant",
        )
        profil = ProfilEtudiant.objects.create(
            utilisateur=user, matricule=f"MIX00{i}", niveau="L1",
            filiere="Info",
        )
        IndicateurAcademique.objects.create(
            etudiant=profil, semestre=None,
            score_risque=score, classification_risque=cls,
            moyenne_generale=10.0, credits_acquis=30, credits_total=180,
        )
        data.append(profil)
    return data


class TestGetScoreEtudiant:
    def test_retourne_dict_avec_cles(self, etudiants_mix):
        """get_score_etudiant doit retourner un dict bien structuré."""
        result = get_score_etudiant(etudiants_mix[0])
        assert "score" in result
        assert "niveau" in result
        assert "indicateurs" in result
        assert "matricule" in result

    def test_score_coherent_avec_persistance(self, etudiants_mix):
        """Le score retourné doit correspondre à l'indicateur persisté."""
        result = get_score_etudiant(etudiants_mix[2])
        assert result["score"] == 75.0
        assert result["niveau"] == "Eleve"

    def test_recalcul_si_indicateur_absent(self, db):
        """Si aucun indicateur persisté, le service doit recalculer."""
        user = Utilisateur.objects.create_user(
            username="new", email="new@test.bf",
            password="TestPass123!", role="etudiant",
        )
        profil = ProfilEtudiant.objects.create(
            utilisateur=user, matricule="NEW001", niveau="L1",
        )
        # Aucun résultat → score calculé (ne doit pas planter)
        result = get_score_etudiant(profil)
        assert "score" in result


class TestGetDistributionScores:
    def test_distribution_3_categories(self, etudiants_mix):
        """La distribution doit compter 1 étudiant par catégorie."""
        dist = get_distribution_scores()
        assert dist["Faible"] == 1
        assert dist["Modere"] == 1
        assert dist["Eleve"] == 1

    def test_distribution_filtre_filiere(self, etudiants_mix):
        """Le filtre par filière doit fonctionner."""
        dist = get_distribution_scores(filiere="Info")
        assert dist["Faible"] + dist["Modere"] + dist["Eleve"] == 3

    def test_distribution_filtre_vide(self, etudiants_mix):
        """Une filière inexistante retourne une distribution vide."""
        dist = get_distribution_scores(filiere="Physique")
        assert dist["Faible"] == 0
        assert dist["Eleve"] == 0


class TestGetUeCritiques:
    def test_ue_critiques_format(self, db):
        """get_ue_critiques doit retourner une liste de dicts."""
        # Crée quelques UE avec résultats
        user = Utilisateur.objects.create_user(
            username="u", email="u@t.bf", password="TestPass123!", role="etudiant",
        )
        etu = ProfilEtudiant.objects.create(
            utilisateur=user, matricule="U001", niveau="L1",
        )
        sem = Semestre.objects.create(numero=1, annee=2025, annee_scolaire="2025-2026")
        ue = UniteEnseignement.objects.create(code="CRIT1", intitule="UE Difficile", credits=6)
        ResultatAcademique.objects.create(
            etudiant=etu, ue=ue, semestre=sem, note=7.0, credits=0, valide=False,
        )
        result = get_ue_critiques(limite=5)
        assert isinstance(result, list)
        assert len(result) >= 1
        first = result[0]
        assert "code" in first
        assert "taux_echec" in first
        assert "effectif" in first

    def test_limite_respectee(self, db):
        """La limite du nombre d'UE doit être respectée."""
        user = Utilisateur.objects.create_user(
            username="u", email="u@t.bf", password="TestPass123!", role="etudiant",
        )
        etu = ProfilEtudiant.objects.create(
            utilisateur=user, matricule="U002", niveau="L1",
        )
        sem = Semestre.objects.create(numero=1, annee=2025, annee_scolaire="2025-2026")
        for i in range(8):
            ue = UniteEnseignement.objects.create(
                code=f"LIM{i}", intitule=f"UE {i}", credits=6,
            )
            ResultatAcademique.objects.create(
                etudiant=etu, ue=ue, semestre=sem, note=8.0, credits=0, valide=False,
            )
        result = get_ue_critiques(limite=3)
        assert len(result) == 3
