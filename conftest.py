"""Configuration pytest globale — fixtures partagées (Phase 13).

Fournit des fixtures réutilisables pour les tests nécessitant une DB :
  - utilisateur_admin : un administrateur
  - utilisateur_etudiant : un utilisateur étudiant + profil
  - ue : une unité d'enseignement
  - semestre : un semestre
  - resultat : un résultat académique
  - etudiant_avec_indicateur : étudiant avec KPI calculés
"""
import pytest

from apps.accounts.models import Utilisateur, ProfilEtudiant
from apps.academics.models import (
    UniteEnseignement, Semestre, ResultatAcademique, Presence,
)
from apps.analytics.models import IndicateurAcademique


@pytest.fixture
def utilisateur_admin(db):
    """Crée un administrateur pour les tests."""
    return Utilisateur.objects.create_user(
        username="admin_test",
        email="admin@test.bf",
        password="TestPass123!",
        first_name="Admin",
        last_name="Test",
        role="administrateur",
        is_staff=True,
    )


@pytest.fixture
def utilisateur_etudiant(db):
    """Crée un utilisateur étudiant + profil."""
    user = Utilisateur.objects.create_user(
        username="etu_test",
        email="etu@test.bf",
        password="TestPass123!",
        first_name="Awa",
        last_name="TEST",
        role="etudiant",
    )
    profil = ProfilEtudiant.objects.create(
        utilisateur=user,
        matricule="TEST0001",
        niveau="L1",
        filiere="Informatique",
        promotion="2025-2026",
        annee_scolaire="2025-2026",
    )
    return profil


@pytest.fixture
def ue(db):
    """Crée une unité d'enseignement."""
    return UniteEnseignement.objects.create(
        code="INF_TEST",
        intitule="UE de test",
        credits=6,
        semestre_numero=1,
    )


@pytest.fixture
def semestre(db):
    """Crée un semestre."""
    return Semestre.objects.create(
        numero=1,
        annee=2025,
        annee_scolaire="2025-2026",
    )


@pytest.fixture
def resultat(db, utilisateur_etudiant, ue, semestre):
    """Crée un résultat académique validé."""
    return ResultatAcademique.objects.create(
        etudiant=utilisateur_etudiant,
        ue=ue,
        semestre=semestre,
        note=14.5,
        credits=6,
        valide=True,
        session="normale",
    )


@pytest.fixture
def etudiant_avec_indicateur(db, utilisateur_etudiant, ue, semestre):
    """Crée un étudiant avec résultats + présence + indicateur calculé."""
    # Résultat validé
    ResultatAcademique.objects.create(
        etudiant=utilisateur_etudiant,
        ue=ue,
        semestre=semestre,
        note=15.0,
        credits=6,
        valide=True,
        session="normale",
    )
    # Résultat non validé
    ue2 = UniteEnseignement.objects.create(
        code="INF_TEST2",
        intitule="UE échec",
        credits=3,
        semestre_numero=1,
    )
    ResultatAcademique.objects.create(
        etudiant=utilisateur_etudiant,
        ue=ue2,
        semestre=semestre,
        note=7.0,
        credits=0,
        valide=False,
        session="normale",
    )
    # Présence
    import datetime
    Presence.objects.create(
        etudiant=utilisateur_etudiant,
        ue=ue,
        date_cours=datetime.date(2025, 10, 15),
        present=True,
    )
    # Indicateur calculé
    IndicateurAcademique.objects.create(
        etudiant=utilisateur_etudiant,
        semestre=None,
        moyenne_generale=11.0,
        score_risque=42.0,
        classification_risque="Modere",
        taux_progression=33.3,
        credits_acquis=6,
        credits_total=180,
        ues_echec=1,
        ues_total=2,
        taux_absenteisme=0.0,
    )
    return utilisateur_etudiant
