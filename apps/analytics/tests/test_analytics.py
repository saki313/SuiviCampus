"""Tests du service de calcul des indicateurs (Phase 13).

Vérifie que calculer_indicateurs_etudiant orchestre correctement :
  - Lecture des résultats OLTP
  - Appel aux formules domain (Eq 2.1 / 2.2)
  - Persistance dans IndicateurAcademique
"""
import datetime

import pytest

from apps.accounts.models import Utilisateur, ProfilEtudiant
from apps.academics.models import (
    UniteEnseignement, Semestre, ResultatAcademique, Presence,
)
from apps.analytics.models import IndicateurAcademique
from apps.analytics.services import (
    calculer_indicateurs_etudiant,
    calculer_indicateurs_promotion,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def etudiant_bon(db):
    """Étudiant avec de bons résultats → faible risque."""
    user = Utilisateur.objects.create_user(
        username="bon", email="bon@test.bf",
        password="TestPass123!", first_name="Bon", last_name="X", role="etudiant",
    )
    profil = ProfilEtudiant.objects.create(
        utilisateur=user, matricule="BON001", niveau="L1", filiere="Info",
    )
    sem = Semestre.objects.create(numero=1, annee=2025, annee_scolaire="2025-2026")
    for i in range(1, 4):
        ue = UniteEnseignement.objects.create(
            code=f"UE_B{i}", intitule=f"UE Bon {i}", credits=6,
        )
        ResultatAcademique.objects.create(
            etudiant=profil, ue=ue, semestre=sem,
            note=16.0, credits=6, valide=True, session="normale",
        )
    return profil


@pytest.fixture
def etudiant_faussE(db):
    """Étudiant en difficulté → risque élevé."""
    user = Utilisateur.objects.create_user(
        username="faible", email="faible@test.bf",
        password="TestPass123!", first_name="Faible", last_name="Y", role="etudiant",
    )
    profil = ProfilEtudiant.objects.create(
        utilisateur=user, matricule="FBL001", niveau="L2", filiere="Info",
    )
    sem = Semestre.objects.create(numero=3, annee=2025, annee_scolaire="2025-2026")
    for i in range(1, 5):
        ue = UniteEnseignement.objects.create(
            code=f"UE_F{i}", intitule=f"UE Faible {i}", credits=6,
        )
        ResultatAcademique.objects.create(
            etudiant=profil, ue=ue, semestre=sem,
            note=7.0, credits=0, valide=False, session="normale",
        )
    return profil


class TestCalculerIndicateursEtudiant:
    def test_etudiant_bon_score_faible(self, etudiant_bon):
        """Un bon étudiant doit avoir un score de risque modéré (pas élevé).

        NB : avec seulement 18/180 crédits validés (L1 débutant), la composante
        crédits (C = 90%) tire le score vers le haut. Le score reste néanmoins
        dans la plage Faible/Modéré (≤ 60), jamais Élevé.
        """
        indic = calculer_indicateurs_etudiant(etudiant_bon)
        assert isinstance(indic, IndicateurAcademique)
        assert indic.score_risque is not None
        assert indic.score_risque <= 60
        assert indic.classification_risque in ("Faible", "Modere")

    def test_etudiant_faible_score_eleve(self, etudiant_faussE):
        """Un étudiant en difficulté doit avoir un score élevé."""
        indic = calculer_indicateurs_etudiant(etudiant_faussE)
        assert indic.score_risque is not None
        assert indic.score_risque > 60
        assert indic.classification_risque == "Eleve"

    def test_persistance_indicateur(self, etudiant_bon):
        """L'indicateur doit être persisté en base."""
        assert IndicateurAcademique.objects.count() == 0
        calculer_indicateurs_etudiant(etudiant_bon)
        assert IndicateurAcademique.objects.count() == 1
        indic = IndicateurAcademique.objects.get(etudiant=etudiant_bon, semestre=None)
        assert indic.moyenne_generale is not None

    def test_calcul_idempotent(self, etudiant_bon):
        """Un second calcul met à jour (update_or_create), ne crée pas de doublon."""
        calculer_indicateurs_etudiant(etudiant_bon)
        calculer_indicateurs_etudiant(etudiant_bon)
        assert IndicateurAcademique.objects.filter(
            etudiant=etudiant_bon, semestre=None
        ).count() == 1

    def test_credits_acquis_coherents(self, etudiant_bon):
        """Les crédits acquis doivent refléter les résultats validés."""
        indic = calculer_indicateurs_etudiant(etudiant_bon)
        # 3 UE × 6 crédits = 18 crédits
        assert indic.credits_acquis == 18

    def test_progression_calculee(self, etudiant_bon):
        """Le taux de progression doit être calculé (Eq 2.2)."""
        indic = calculer_indicateurs_etudiant(etudiant_bon)
        assert indic.taux_progression is not None
        assert 0 <= indic.taux_progression <= 100


class TestCalculerIndicateursPromotion:
    def test_recalcule_tous_etudiants(self, etudiant_bon, etudiant_faussE):
        """calculer_indicateurs_promotion traite tous les étudiants."""
        count = calculer_indicateurs_promotion()
        assert count == 2
        assert IndicateurAcademique.objects.count() == 2
