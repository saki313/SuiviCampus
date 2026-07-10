"""Tests unitaires de la progression/diplomation — Eq 2.2 (domain pur, sans DB)."""
from datetime import date

import pytest

from domain.kpi.progression import (
    calculer_credits_moyen_par_semestre,
    calculer_progression_complet,
    calculer_projection_diplomation,
    calculer_semestres_restants,
    calculer_taux_progression,
)


class TestTauxProgression:
    def test_aucun_credit_acquis(self):
        assert calculer_taux_progression(0, 120) == 0.0

    def test_tous_credits_acquis(self):
        assert calculer_taux_progression(120, 120) == 100.0

    def test_credits_partiels(self):
        # 90/120 → 75%
        assert calculer_taux_progression(90, 120) == pytest.approx(75.0)

    def test_credits_total_nul(self):
        assert calculer_taux_progression(60, 0) == 0.0

    def test_clamp_cent_pourcent(self):
        # c_acq > c_total → clampé à 100
        assert calculer_taux_progression(150, 120) == 100.0


class TestCreditsMoyenParSemestre:
    def test_aucun_semestre_valide(self):
        # division par zéro évitée
        assert calculer_credits_moyen_par_semestre(60, 0) == 0.0

    def test_moyenne_simple(self):
        # 60 crédits sur 2 semestres → 30
        assert calculer_credits_moyen_par_semestre(60, 2) == pytest.approx(30.0)

    def test_moyenne_decimale(self):
        # 90 crédits sur 4 semestres → 22,5
        assert calculer_credits_moyen_par_semestre(90, 4) == pytest.approx(22.5)


class TestSemestresRestants:
    def test_etudiant_deja_diplome(self):
        # c_acq >= c_total → 0
        assert calculer_semestres_restants(120, 120, 30) == 0.0

    def test_moyenne_nulle(self):
        # c̄_sem = 0 → 0 (évite division par zéro)
        assert calculer_semestres_restants(60, 120, 0) == 0.0

    def test_formule_exacte(self):
        # (120 − 60) / 30 = 2 semestres
        assert calculer_semestres_restants(60, 120, 30) == pytest.approx(2.0)

    def test_formule_decimale(self):
        # (120 − 90) / 22,5 = 1,33...
        assert calculer_semestres_restants(90, 120, 22.5) == pytest.approx(30 / 22.5)


class TestProjectionDiplomation:
    def test_semestres_restants_nuls(self):
        # déjà diplômé → projection = date de référence
        ref = date(2025, 1, 1)
        assert calculer_projection_diplomation(0, ref) == ref

    def test_un_semestre_restant(self):
        # 1 semestre ≈ 183 jours après ref
        ref = date(2025, 1, 1)
        proj = calculer_projection_diplomation(1, ref)
        assert proj == ref.replace(year=ref.year) + __import__("datetime").timedelta(days=183)

    def test_deux_semestres_restants(self):
        # 2 semestres ≈ 366 jours
        ref = date(2025, 1, 1)
        from datetime import timedelta
        proj = calculer_projection_diplomation(2, ref)
        assert proj == ref + timedelta(days=366)


class TestPipelineComplet:
    def test_etudiant_50_pourcent_maquette(self):
        # Maquette mémoire : barre de progression 50%, projection juin 2026
        res = calculer_progression_complet(
            credits_acquis=60,
            credits_total=120,
            semestres_valides=2,
            date_reference=date(2025, 1, 1),
        )
        assert res.taux_progression == pytest.approx(50.0)
        assert res.credits_moyen_par_semestre == pytest.approx(30.0)
        assert res.semestres_restants == pytest.approx(2.0)
        assert res.projection_diplomation is not None

    def test_etudiant_diplome(self):
        res = calculer_progression_complet(
            credits_acquis=120, credits_total=120,
            semestres_valides=4, date_reference=date(2025, 6, 1),
        )
        assert res.taux_progression == 100.0
        assert res.semestres_restants == 0.0
