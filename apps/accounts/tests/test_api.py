"""Tests de l'API REST — authentification JWT et permissions RBAC (Phase 13).

Vérifie :
  - L'authentification JWT (obtention + refresh de token)
  - Le contrôle d'accès par rôle (RBAC)
  - Les endpoints API répondent correctement
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Utilisateur, ProfilEtudiant


pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    """Client API non authentifié."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    return Utilisateur.objects.create_user(
        username="admin", email="admin@test.bf",
        password="TestPass123!", first_name="Admin", last_name="S",
        role="administrateur", is_staff=True,
    )


@pytest.fixture
def etudiant_user(db):
    user = Utilisateur.objects.create_user(
        username="etu", email="etu@test.bf",
        password="TestPass123!", first_name="Etu", last_name="D",
        role="etudiant",
    )
    ProfilEtudiant.objects.create(
        utilisateur=user, matricule="API001", niveau="L1", filiere="Info",
    )
    return user


@pytest.fixture
def auth_client_etudiant(etudiant_user):
    """Client API authentifié en tant qu'étudiant."""
    client = APIClient()
    refresh = RefreshToken.for_user(etudiant_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def auth_client_admin(admin_user):
    """Client API authentifié en tant qu'administrateur."""
    client = APIClient()
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


class TestAuthJWT:
    """Tests du flow JWT (BF12)."""

    def test_obtention_token(self, api_client, etudiant_user):
        """POST /api/auth/login/ doit retourner un access + refresh token."""
        url = reverse("auth:token_obtain_pair")
        resp = api_client.post(url, {
            "username": "etu",
            "password": "TestPass123!",
        }, format="json")
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_refresh_token(self, api_client, etudiant_user):
        """POST /api/auth/refresh/ doit retourner un nouveau access token."""
        refresh = RefreshToken.for_user(etudiant_user)
        url = reverse("auth:token_refresh")
        resp = api_client.post(url, {"refresh": str(refresh)}, format="json")
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_identifiants_invalides(self, api_client):
        """Des identifiants invalides doivent retourner 401."""
        url = reverse("auth:token_obtain_pair")
        resp = api_client.post(url, {
            "username": "inexistant",
            "password": "faux",
        }, format="json")
        assert resp.status_code == 401


class TestPermissionsRBAC:
    """Tests du contrôle d'accès par rôle (BF12)."""

    def test_endpoint_sans_auth_redirige(self, api_client):
        """Un endpoint protégé sans authentification doit retourner 401."""
        url = reverse("accounts_api:etudiant-list")
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_etudiant_voit_son_profil(self, auth_client_etudiant, etudiant_user):
        """Un étudiant authentifié peut consulter les profils étudiant."""
        url = reverse("accounts_api:etudiant-list")
        resp = auth_client_etudiant.get(url)
        assert resp.status_code == 200
        # Un étudiant ne voit que son propre profil
        results = resp.data.get("results", resp.data)
        assert len(results) == 1

    def test_admin_voit_tous_profils(self, auth_client_admin, etudiant_user):
        """Un admin peut consulter tous les profils étudiant."""
        url = reverse("accounts_api:etudiant-list")
        resp = auth_client_admin.get(url)
        assert resp.status_code == 200


class TestEndpointAPI:
    """Tests de base des endpoints API principaux."""

    def test_endpoint_indicateurs(self, auth_client_admin):
        """GET /api/indicateurs/ doit répondre 200."""
        url = reverse("analytics_api:indicateur-list")
        resp = auth_client_admin.get(url)
        assert resp.status_code == 200

    def test_endpoint_etudiants(self, auth_client_admin):
        """GET /api/etudiants/ doit répondre 200."""
        url = reverse("accounts_api:etudiant-list")
        resp = auth_client_admin.get(url)
        assert resp.status_code == 200

    def test_endpoint_ues(self, auth_client_admin):
        """GET /api/ue/ doit répondre 200."""
        url = reverse("academics_api:ue-list")
        resp = auth_client_admin.get(url)
        assert resp.status_code == 200

    def test_endpoint_resultats(self, auth_client_admin):
        """GET /api/resultats/ doit répondre 200."""
        url = reverse("academics_api:resultat-list")
        resp = auth_client_admin.get(url)
        assert resp.status_code == 200
