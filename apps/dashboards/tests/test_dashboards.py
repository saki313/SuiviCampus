"""Tests des vues web des dashboards (Phase 13).

Vérifie :
  - L'accès aux dashboards selon le rôle (RBAC)
  - La redirection par rôle après login
  - Le téléchargement des rapports (PDF/Excel/CSV)
"""
import pytest
from django.urls import reverse
from django.test import Client

from apps.accounts.models import Utilisateur, ProfilEtudiant


pytestmark = pytest.mark.django_db


@pytest.fixture
def client_web():
    """Client HTTP non authentifié."""
    return Client()


@pytest.fixture
def etudiant_web(db):
    """Étudiant authentifié via session."""
    user = Utilisateur.objects.create_user(
        username="webetu", email="webetu@test.bf",
        password="TestPass123!", first_name="Web", last_name="Etu",
        role="etudiant",
    )
    ProfilEtudiant.objects.create(
        utilisateur=user, matricule="WEB001", niveau="L1", filiere="Info",
    )
    return user


@pytest.fixture
def admin_web(db):
    """Administrateur authentifié via session."""
    return Utilisateur.objects.create_user(
        username="webadmin", email="webadmin@test.bf",
        password="TestPass123!", first_name="Web", last_name="Admin",
        role="administrateur", is_staff=True,
    )


class TestAuthentification:
    """Tests du login/logout web."""

    def test_page_login_accessible(self, client_web):
        """La page de login doit être accessible sans auth."""
        resp = client_web.get(reverse("dashboards:login"))
        assert resp.status_code == 200

    def test_login_etudiant_redirige_dashboard(self, client_web, etudiant_web):
        """Un étudiant qui se connecte est redirigé vers son dashboard."""
        resp = client_web.post(reverse("dashboards:login"), {
            "username": "webetu",
            "password": "TestPass123!",
        })
        assert resp.status_code == 302
        assert "/tableau-de-bord/" in resp.url

    def test_login_admin_redirige_etl(self, client_web, admin_web):
        """Un admin est redirigé vers la supervision ETL."""
        resp = client_web.post(reverse("dashboards:login"), {
            "username": "webadmin",
            "password": "TestPass123!",
        })
        assert resp.status_code == 302
        assert "/admin/etl/" in resp.url

    def test_login_identifiants_invalides(self, client_web):
        """Identifiants invalides → reste sur login avec erreur."""
        resp = client_web.post(reverse("dashboards:login"), {
            "username": "faux",
            "password": "faux",
        })
        assert resp.status_code == 200  # reste sur la page
        assert "error" in resp.context or "invalides" in resp.content.decode().lower()

    def test_dashboard_sans_auth_redirige_login(self, client_web):
        """Accès au dashboard sans auth → redirection login."""
        resp = client_web.get(reverse("dashboards:etudiant"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_dashboard_sans_auth_utilise_la_page_login_du_projet(self, client_web):
        """La redirection doit pointer vers /login/ et non vers /accounts/login/."""
        resp = client_web.get(reverse("dashboards:etudiant"))
        assert resp.status_code == 302
        assert resp.url.startswith("/login/")
        assert "/accounts/login/" not in resp.url


class TestDashboardsParRole:
    """Tests des dashboards selon le rôle."""

    def test_dashboard_etudiant_auth(self, client_web, etudiant_web):
        """L'étudiant authentifié accède à son dashboard."""
        client_web.force_login(etudiant_web)
        resp = client_web.get(reverse("dashboards:etudiant"))
        assert resp.status_code == 200

    def test_dashboard_admin_etl(self, client_web, admin_web):
        """L'admin accède à la supervision ETL."""
        client_web.force_login(admin_web)
        resp = client_web.get(reverse("dashboards:admin_etl"))
        assert resp.status_code == 200

    def test_dashboard_admin_utilisateurs(self, client_web, admin_web):
        """L'admin accède à la gestion des utilisateurs."""
        client_web.force_login(admin_web)
        resp = client_web.get(reverse("dashboards:admin_utilisateurs"))
        assert resp.status_code == 200

    def test_dashboard_admin_parametres(self, client_web, admin_web):
        """L'admin accède aux paramètres d'alerte."""
        client_web.force_login(admin_web)
        resp = client_web.get(reverse("dashboards:admin_parametres"))
        assert resp.status_code == 200

    def test_dashboard_admin_audit(self, client_web, admin_web):
        """L'admin accède au journal d'audit."""
        client_web.force_login(admin_web)
        resp = client_web.get(reverse("dashboards:admin_audit"))
        assert resp.status_code == 200


class TestTelechargementRapports:
    """Tests du téléchargement des rapports (Phase 12)."""

    def test_telechargement_pdf(self, client_web, admin_web):
        """Le téléchargement PDF doit retourner un fichier application/pdf."""
        client_web.force_login(admin_web)
        resp = client_web.get(reverse("dashboards:rapport_pdf"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"

    def test_telechargement_excel(self, client_web, admin_web):
        """Le téléchargement Excel doit retourner un fichier xlsx."""
        client_web.force_login(admin_web)
        resp = client_web.get(reverse("dashboards:rapport_excel"))
        assert resp.status_code == 200
        assert resp.content[:4] == b"PK\x03\x04"

    def test_telechargement_csv(self, client_web, admin_web):
        """Le téléchargement CSV doit retourner du texte CSV."""
        client_web.force_login(admin_web)
        resp = client_web.get(reverse("dashboards:rapport_csv"))
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"matricule" in resp.content

    def test_telechargement_sans_auth_redirige(self, client_web):
        """Téléchargement sans auth → redirection login."""
        resp = client_web.get(reverse("dashboards:rapport_pdf"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_telechargement_filtre_niveau(self, client_web, admin_web):
        """Le filtre niveau doit être pris en compte sans erreur."""
        client_web.force_login(admin_web)
        resp = client_web.get(reverse("dashboards:rapport_pdf") + "?niveau=L1")
        assert resp.status_code == 200
