"""Tests unitaires du score de risque — Eq 2.1 exacte (domain pur, sans DB).

Vérifie :
  - les 4 indicateurs individuels (N, C, U, A)
  - la formule composite exacte
  - le bornage [0; 100]
  - la classification Faible/Modéré/Élevé
"""
import pytest

from domain.kpi.score_risque import (
    calculer_indicateurs,
    calculer_score,
    calculer_score_complet,
    classifier_score,
    indicateur_absenteisme,
    indicateur_credits,
    indicateur_notes,
    indicateur_ue_echec,
    PONDERATIONS_DEFAUT,
    Ponderations,
)


# ---------------------------------------------------------------------------
# Indicateur notes : N = (1 − m̄/20) × 100
# ---------------------------------------------------------------------------

class TestIndicateurNotes:
    def test_moyenne_maximale_20(self):
        # m̄ = 20 → risque note nul → N = 0
        assert indicateur_notes(20) == 0.0

    def test_moyenne_nulle_0(self):
        # m̄ = 0 → risque note maximal → N = 100
        assert indicateur_notes(0) == 100.0

    def test_moyenne_10(self):
        # m̄ = 10 → (1 − 0,5) × 100 = 50
        assert indicateur_notes(10) == pytest.approx(50.0)

    def test_moyenne_none(self):
        # m̄ = None → N = 0 (pas de donnée)
        assert indicateur_notes(None) == 0.0

    def test_clamp_hors_bornes(self):
        # m̄ > 20 clampé à 20 → N = 0 ; m̄ < 0 clampé à 0 → N = 100
        assert indicateur_notes(25) == 0.0
        assert indicateur_notes(-5) == 100.0


# ---------------------------------------------------------------------------
# Indicateur credits : C = (1 − c_acq/c_total) × 100
# ---------------------------------------------------------------------------

class TestIndicateurCredits:
    def test_tous_credits_acquis(self):
        # c_acq = c_total → C = 0
        assert indicateur_credits(120, 120) == 0.0

    def test_aucun_credit_acquis(self):
        # c_acq = 0 → C = 100
        assert indicateur_credits(0, 120) == 100.0

    def test_credits_partiels(self):
        # 90/120 → (1 − 0,75) × 100 = 25
        assert indicateur_credits(90, 120) == pytest.approx(25.0)

    def test_credits_total_nul(self):
        # c_total = 0 → évite division par zéro → C = 0
        assert indicateur_credits(0, 0) == 0.0

    def test_credits_acquis_superieur_total_clamp(self):
        # c_acq > c_total → clamp à 0
        assert indicateur_credits(150, 120) == 0.0


# ---------------------------------------------------------------------------
# Indicateur UE echec : U = (u_echec/u_total) × 100
# ---------------------------------------------------------------------------

class TestIndicateurUEEchec:
    def test_aucun_echec(self):
        assert indicateur_ue_echec(0, 10) == 0.0

    def test_toutes_ue_echec(self):
        assert indicateur_ue_echec(10, 10) == 100.0

    def test_echec_partiel(self):
        # 3/10 → 30
        assert indicateur_ue_echec(3, 10) == pytest.approx(30.0)

    def test_total_nul(self):
        assert indicateur_ue_echec(0, 0) == 0.0


# ---------------------------------------------------------------------------
# Indicateur absenteisme : A = (1 − s_pres/s_tot) × 100
# ---------------------------------------------------------------------------

class TestIndicateurAbsenteisme:
    def test_toujours_present(self):
        assert indicateur_absenteisme(100, 100) == 0.0

    def test_toujours_absent(self):
        assert indicateur_absenteisme(0, 100) == 100.0

    def test_absenteisme_partiel(self):
        # 80/100 présents → (1 − 0,8) × 100 = 20
        assert indicateur_absenteisme(80, 100) == pytest.approx(20.0)

    def test_sessions_nulles(self):
        assert indicateur_absenteisme(0, 0) == 0.0


# ---------------------------------------------------------------------------
# Score composite : Eq 2.1 exacte
# ---------------------------------------------------------------------------

class TestScoreComposite:
    def test_score_borne_0_100(self):
        # Cas extrême : tout au pire → score = 100
        ind = calculer_indicateurs(
            moyenne_generale=0, credits_acquis=0, credits_total=120,
            ues_echec=10, ues_total=10, sessions_presentes=0, sessions_total=100,
        )
        assert calculer_score(ind) == pytest.approx(100.0)

    def test_score_borne_0(self):
        # Cas idéal : tout au mieux → score = 0
        ind = calculer_indicateurs(
            moyenne_generale=20, credits_acquis=120, credits_total=120,
            ues_echec=0, ues_total=10, sessions_presentes=100, sessions_total=100,
        )
        assert calculer_score(ind) == pytest.approx(0.0)

    def test_formule_exacte_eq21(self):
        # N=50, C=25, U=30, A=20 → score = 0,4×50 + 0,3×25 + 0,2×30 + 0,1×20
        #                                  = 20 + 7,5 + 6 + 2 = 35,5
        ind = calculer_indicateurs(
            moyenne_generale=10, credits_acquis=90, credits_total=120,
            ues_echec=3, ues_total=10, sessions_presentes=80, sessions_total=100,
        )
        score = calculer_score(ind)
        assert score == pytest.approx(35.5)

    def test_ponderations_somme_un(self):
        # Preuve de bornage : Σcoeff = 1
        total = (
            PONDERATIONS_DEFAUT.notes
            + PONDERATIONS_DEFAUT.credits
            + PONDERATIONS_DEFAUT.ue_echec
            + PONDERATIONS_DEFAUT.absenteisme
        )
        assert total == pytest.approx(1.0)

    def test_ponderations_personnalisees(self):
        # Si on change les pondérations, le score change proportionnellement
        ind = calculer_indicateurs(
            moyenne_generale=10, credits_acquis=60, credits_total=120,
            ues_echec=2, ues_total=10, sessions_presentes=50, sessions_total=100,
        )
        score_defaut = calculer_score(ind)
        # Pondérations 100% sur notes → score = N
        pond_notes = Ponderations(notes=1.0, credits=0.0, ue_echec=0.0, absenteisme=0.0)
        assert calculer_score(ind, pond_notes) == pytest.approx(ind.notes)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

class TestClassification:
    @pytest.mark.parametrize("score, attendu", [
        (0, "Faible"),
        (15, "Faible"),
        (30, "Faible"),       # limite supérieure Faible (inclusive)
        (31, "Modere"),
        (45, "Modere"),
        (60, "Modere"),       # limite supérieure Modéré (inclusive)
        (61, "Eleve"),
        (80, "Eleve"),
        (100, "Eleve"),
    ])
    def test_classifications_limites(self, score, attendu):
        assert classifier_score(score) == attendu


# ---------------------------------------------------------------------------
# Pipeline complet
# ---------------------------------------------------------------------------

class TestPipelineComplet:
    def test_score_complet_cohérent_maquette(self):
        # Cas réaliste : étudiant moyen (maquette TB étudiant score=42)
        res = calculer_score_complet(
            moyenne_generale=11.5,   # m̄ proche de 11,5
            credits_acquis=90, credits_total=120,
            ues_echec=2, ues_total=12,
            sessions_presentes=85, sessions_total=100,
        )
        # Score doit être dans [0; 100]
        assert 0 <= res.score <= 100
        # Classification cohérente avec le score
        assert res.classification == classifier_score(res.score)
        # Indicateurs tous dans [0; 100]
        for ind in res.indicateurs:
            assert 0 <= ind <= 100
