"""Tests du service Gestionnaire d'Alertes (Phase 13).

Vérifie la génération d'alertes selon les seuils, la non-duplication,
le traitement et l'archivage.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.accounts.models import Utilisateur, ProfilEtudiant
from apps.analytics.models import IndicateurAcademique
from apps.alerts.models import Alerte, ParametreAlerte, Recommandation
from apps.alerts.services import (
    get_parametres_actifs,
    generer_alerte,
    verifier_et_generer_alertes,
    traiter_alerte,
    archiver_anciennes_alertes,
)
from apps.common.enums import NiveauRisque, StatutAlerte, TypeAlerte


pytestmark = pytest.mark.django_db


@pytest.fixture
def etudiant_risque(db):
    """Crée un étudiant avec un indicateur de risque élevé."""
    user = Utilisateur.objects.create_user(
        username="etu_risque",
        email="risque@test.bf",
        password="TestPass123!",
        first_name="Risque",
        last_name="TEST",
        role="etudiant",
    )
    profil = ProfilEtudiant.objects.create(
        utilisateur=user,
        matricule="RISK0001",
        niveau="L2",
        filiere="Informatique",
    )
    IndicateurAcademique.objects.create(
        etudiant=profil,
        semestre=None,
        moyenne_generale=7.0,
        score_risque=75.0,
        classification_risque="Eleve",
        taux_progression=20.0,
        credits_acquis=10,
        credits_total=180,
        ues_echec=4,
        ues_total=6,
        taux_absenteisme=40.0,
    )
    return profil


@pytest.fixture
def etudiant_sain(db):
    """Crée un étudiant sans risque."""
    user = Utilisateur.objects.create_user(
        username="etu_sain",
        email="sain@test.bf",
        password="TestPass123!",
        first_name="Sain",
        last_name="TEST",
        role="etudiant",
    )
    profil = ProfilEtudiant.objects.create(
        utilisateur=user,
        matricule="SAIN0001",
        niveau="L1",
        filiere="Informatique",
    )
    IndicateurAcademique.objects.create(
        etudiant=profil,
        semestre=None,
        moyenne_generale=15.0,
        score_risque=15.0,
        classification_risque="Faible",
        taux_progression=60.0,
        credits_acquis=100,
        credits_total=180,
        ues_echec=0,
        ues_total=6,
        taux_absenteisme=5.0,
    )
    return profil


class TestParametresActifs:
    def test_creation_si_absent(self, db):
        """get_parametres_actifs crée les paramètres par défaut s'ils n'existent pas."""
        assert ParametreAlerte.objects.count() == 0
        params = get_parametres_actifs()
        assert params is not None
        assert params.seuil_faible == 30.0
        assert params.seuil_modere == 60.0
        assert params.ponderation_notes == 0.40

    def test_reutilisation_si_existant(self, db):
        """get_parametres_actifs réutilise les paramètres existants."""
        ParametreAlerte.objects.create(seuil_faible=25.0, seuil_modere=55.0)
        params = get_parametres_actifs()
        assert params.seuil_faible == 25.0
        assert ParametreAlerte.objects.count() == 1


class TestGenererAlerte:
    def test_creation_alerte(self, etudiant_risque):
        """generer_alerte crée une alerte + une recommandation."""
        alerte = generer_alerte(
            etudiant_risque, TypeAlerte.RISQUE, NiveauRisque.ELEVE, 75.0
        )
        assert alerte is not None
        assert alerte.statut == StatutAlerte.ACTIVE
        assert alerte.score_risque == 75.0
        # Une recommandation associée
        assert alerte.recommandations.count() == 1

    def test_non_duplication(self, etudiant_risque):
        """Une alerte active du même type n'est pas dupliquée."""
        a1 = generer_alerte(etudiant_risque, TypeAlerte.RISQUE, NiveauRisque.ELEVE, 75.0)
        a2 = generer_alerte(etudiant_risque, TypeAlerte.RISQUE, NiveauRisque.ELEVE, 75.0)
        assert a1 is not None
        assert a2 is None  # pas de duplication
        assert Alerte.objects.filter(etudiant=etudiant_risque).count() == 1


class TestVerifierEtGenerer:
    def test_etudiant_risque_genere_alertes(self, etudiant_risque):
        """Un étudiant à risque élevé doit déclencher plusieurs alertes."""
        alertes = verifier_et_generer_alertes(etudiant_risque)
        # Score > 60 → RISQUE ; UE échec 4/6 > 30% → ECHEC_UE ;
        # crédits 10/180 < 50% → CREDITS ; abs > 30% → ABSENCE
        assert len(alertes) >= 3
        types = [a.type for a in alertes]
        assert TypeAlerte.RISQUE in types

    def test_etudiant_sain_sans_alerte(self, etudiant_sain):
        """Un étudiant sans risque ne déclenche aucune alerte."""
        alertes = verifier_et_generer_alertes(etudiant_sain)
        assert len(alertes) == 0

    def test_sans_indicateur_retourne_vide(self, db):
        """Sans indicateur calculé, aucune alerte n'est générée."""
        user = Utilisateur.objects.create_user(
            username="etu_sans", email="sans@test.bf",
            password="TestPass123!", role="etudiant",
        )
        profil = ProfilEtudiant.objects.create(
            utilisateur=user, matricule="NOK0001", niveau="L1",
        )
        alertes = verifier_et_generer_alertes(profil)
        assert alertes == []


class TestTraiterEtArchiver:
    def test_traiter_alerte(self, etudiant_risque, db):
        """traiter_alerte marque l'alerte comme traitée."""
        user = Utilisateur.objects.create_user(
            username="resp", email="resp@test.bf",
            password="TestPass123!", role="responsable",
        )
        alerte = generer_alerte(
            etudiant_risque, TypeAlerte.RISQUE, NiveauRisque.ELEVE, 75.0
        )
        traiter_alerte(alerte, user)
        alerte.refresh_from_db()
        assert alerte.statut == StatutAlerte.TRAITEE
        assert alerte.traitee_par == user
        assert alerte.date_traitement is not None

    def test_archiver_anciennes(self, etudiant_risque, db):
        """archiver_anciennes_alertes archive les alertes traitées anciennes."""
        alerte = generer_alerte(
            etudiant_risque, TypeAlerte.RISQUE, NiveauRisque.ELEVE, 75.0
        )
        alerte.statut = StatutAlerte.TRAITEE
        alerte.date_traitement = timezone.now() - timedelta(days=100)
        alerte.save()

        count = archiver_anciennes_alertes(jours=90)
        assert count == 1
        alerte.refresh_from_db()
        assert alerte.statut == StatutAlerte.ARCHIVEE
